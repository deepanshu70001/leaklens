"""
Extraction service — regex parsers for SMS/email/statements + Groq fallback (§4, §7).
"""
import re
from datetime import datetime
from typing import Optional
import pandas as pd
from app.services.groq_client import extract_transaction_from_text


# ── Regex patterns for common Indian bank SMS formats ────────────────

# Pattern 1: "Your a/c XX4521 debited INR 199.00 on 15-Jan-2024 for NETFLIX.COM"
PATTERN_BANK_DEBIT = re.compile(
    r'(?:a/c|acct?|account)\s*[A-Z]*(\w+)\s+debited\s+'
    r'(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)\s+'
    r'on\s+(\d{1,2}[-/]\w{3}[-/]\d{2,4})\s+'
    r'(?:for|at)\s+(.+?)(?:\.\s*(?:Avl|Bal|Available)|\s*$)',
    re.IGNORECASE
)

# Pattern 2: "UPI/P2M/412345678/AMAZONPRIME/amazon@apl: Rs.1499.00 debited from a/c XX4521 on 10-Jan-2024"
PATTERN_UPI = re.compile(
    r'UPI/P2M/\d+/([^/]+)/[^:]+:\s*(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)\s+'
    r'debited\s+from\s+a/c\s+\w+\s+on\s+(\d{1,2}[-/]\w{3}[-/]\d{2,4})',
    re.IGNORECASE
)

# Pattern 3: "HDFC Bank: Rs.499.00 debited from a/c XXXX1234 on 08-Jan-2024 at HOTSTAR PREMIUM"
PATTERN_BANK_AT = re.compile(
    r'(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)\s+'
    r'(?:debited|charged)\s+(?:from|to)\s+(?:a/c|card)\s+\w+\s+'
    r'on\s+(\d{1,2}[-/]\w{3}[-/]\d{2,4})\s+'
    r'(?:at|for)\s+(.+?)(?:\.\s*(?:Avl|Bal|Ref)|\s*$)',
    re.IGNORECASE
)

# Pattern 4: "ICICI: INR 2,499.00 charged to card XX8876 on 15-Jan-2024 for MICROSOFT 365. Ref#TXN9012345"
PATTERN_CARD_CHARGE = re.compile(
    r'(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)\s+'
    r'charged\s+to\s+card\s+\w+\s+'
    r'on\s+(\d{1,2}[-/]\w{3}[-/]\d{2,4})\s+'
    r'for\s+(.+?)(?:\.\s*Ref|\s*$)',
    re.IGNORECASE
)

# Pattern 5: "PAYPAL *NORDVPN: Rs.350.00 debited from a/c XXXX1234 on 02-Jan-2024. Bal: Rs.33,000.00"
PATTERN_PAYPAL = re.compile(
    r'(?:PAYPAL\s*\*?\s*)(.+?):\s*(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)\s+'
    r'debited\s+from\s+a/c\s+\w+\s+on\s+(\d{1,2}[-/]\w{3}[-/]\d{2,4})',
    re.IGNORECASE
)

# Pattern 6: "SBI Alert: Rs.199.00 debited from a/c XX6789 on 10-Feb-2024 for GOOGLE ONE STORAGE. Ref 998877"
PATTERN_SBI = re.compile(
    r'(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)\s+'
    r'debited\s+from\s+a/c\s+\w+\s+'
    r'on\s+(\d{1,2}[-/]\w{3}[-/]\d{2,4})\s+'
    r'for\s+(.+?)(?:\.\s*Ref|\s*$)',
    re.IGNORECASE
)

# Pattern 7: "Congratulations! Automatic payment of Rs.139 for Apple Media Services has been setup successfully - Paytm"
PATTERN_AUTOPAY_SETUP = re.compile(
    r'(?:Automatic\s+payment|Autopay|Mandate)\s+(?:of|for)?\s*(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)\s+'
    r'for\s+(.+?)\s+has\s+been\s+(?:setup|created|registered)',
    re.IGNORECASE
)


def _parse_amount(amount_str: str) -> float:
    """Parse amount string like '1,499.00' to float."""
    return float(amount_str.replace(",", ""))


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse date strings in various formats."""
    formats = [
        "%d-%b-%Y",   # 15-Jan-2024
        "%d/%b/%Y",   # 15/Jan/2024
        "%d-%m-%Y",   # 15-01-2024
        "%d/%m/%Y",   # 15/01/2024
        "%Y-%m-%d",   # 2024-01-15
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_sms_line(line: str) -> Optional[dict]:
    """
    Try to parse a single SMS/alert line using regex patterns.
    Returns {merchant, amount, currency, date} or None.
    """
    line = line.strip()
    if not line:
        return None

    # Try Pattern 1: Bank debit
    m = PATTERN_BANK_DEBIT.search(line)
    if m:
        return {
            "merchant": m.group(4).strip(),
            "amount": _parse_amount(m.group(2)),
            "currency": "INR",
            "date": _parse_date(m.group(3)),
            "raw_text": line,
        }

    # Try Pattern 2: UPI
    m = PATTERN_UPI.search(line)
    if m:
        return {
            "merchant": m.group(1).strip(),
            "amount": _parse_amount(m.group(2)),
            "currency": "INR",
            "date": _parse_date(m.group(3)),
            "raw_text": line,
        }

    # Try Pattern 5: PayPal (before Pattern 3 to avoid partial match)
    m = PATTERN_PAYPAL.search(line)
    if m:
        return {
            "merchant": m.group(1).strip(),
            "amount": _parse_amount(m.group(2)),
            "currency": "INR",
            "date": _parse_date(m.group(3)),
            "raw_text": line,
        }

    # Try Pattern 3: Bank at
    m = PATTERN_BANK_AT.search(line)
    if m:
        return {
            "merchant": m.group(3).strip(),
            "amount": _parse_amount(m.group(1)),
            "currency": "INR",
            "date": _parse_date(m.group(2)),
            "raw_text": line,
        }

    # Try Pattern 4: Card charge
    m = PATTERN_CARD_CHARGE.search(line)
    if m:
        return {
            "merchant": m.group(3).strip(),
            "amount": _parse_amount(m.group(1)),
            "currency": "INR",
            "date": _parse_date(m.group(2)),
            "raw_text": line,
        }

    # Try Pattern 6: SBI
    m = PATTERN_SBI.search(line)
    if m:
        return {
            "merchant": m.group(3).strip(),
            "amount": _parse_amount(m.group(1)),
            "currency": "INR",
            "date": _parse_date(m.group(2)),
            "raw_text": line,
        }

    # Try Pattern 7: Auto-pay Setup
    m = PATTERN_AUTOPAY_SETUP.search(line)
    if m:
        # Auto-pay setup might not have a date explicitly in the text (like this example), 
        # so we fallback to today's date if missing.
        return {
            "merchant": m.group(2).strip(),
            "amount": _parse_amount(m.group(1)),
            "currency": "INR",
            "date": datetime.now(),
            "raw_text": line,
            "is_explicit_setup": True, # Flag it for the recurring detector
        }

    return None


async def parse_sms_text(raw_text: str) -> list[dict]:
    """
    Parse multi-line SMS text. Uses regex first, falls back to Groq for unparseable lines.
    """
    results = []
    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]

    for line in lines:
        parsed = parse_sms_line(line)
        if parsed and parsed.get("merchant") and parsed.get("amount"):
            results.append(parsed)
        else:
            # Groq fallback for lines regex can't handle
            groq_result = await extract_transaction_from_text(line)
            if groq_result and groq_result.get("merchant") and groq_result.get("amount"):
                date = None
                if groq_result.get("date"):
                    date = _parse_date(groq_result["date"])
                results.append({
                    "merchant": groq_result["merchant"],
                    "amount": float(groq_result["amount"]),
                    "currency": groq_result.get("currency", "INR"),
                    "date": date or datetime.now(),
                    "raw_text": line,
                    "is_explicit_setup": any(kw in line.lower() for kw in ["automatic payment", "auto-pay", "autopay", "mandate", "subscription setup"]),
                })

    return results


def parse_csv_statement(csv_content: str) -> list[dict]:
    """
    Parse a CSV bank statement. Expects columns: Date, Description, Debit, Credit, Balance.
    Only processes debit (expense) rows.
    """
    from io import StringIO
    results = []

    try:
        df = pd.read_csv(StringIO(csv_content))

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]

        # Find the relevant columns
        date_col = next((c for c in df.columns if 'date' in c), None)
        desc_col = next((c for c in df.columns if 'desc' in c or 'narr' in c or 'particular' in c), None)
        debit_col = next((c for c in df.columns if 'debit' in c or 'withdrawal' in c), None)

        if not all([date_col, desc_col, debit_col]):
            return results

        for _, row in df.iterrows():
            debit_val = row.get(debit_col)
            if pd.isna(debit_val) or float(debit_val) == 0:
                continue

            date = _parse_date(str(row[date_col]))
            if not date:
                continue

            results.append({
                "merchant": str(row[desc_col]).strip(),
                "amount": float(debit_val),
                "currency": "INR",
                "date": date,
                "raw_text": str(row[desc_col]),
            })
    except Exception as e:
        print(f"CSV parsing error: {e}")

    return results


def parse_pdf_statement(pdf_bytes: bytes) -> list[dict]:
    """
    Parse a PDF bank statement using pdfplumber.
    Extracts tables and attempts to parse transaction rows.
    """
    import pdfplumber
    from io import BytesIO

    results = []
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Use first row as headers
                    headers = [str(h).strip().lower() if h else "" for h in table[0]]
                    date_idx = next((i for i, h in enumerate(headers) if 'date' in h), None)
                    desc_idx = next((i for i, h in enumerate(headers) if 'desc' in h or 'narr' in h or 'particular' in h), None)
                    debit_idx = next((i for i, h in enumerate(headers) if 'debit' in h or 'withdrawal' in h), None)

                    if date_idx is None or desc_idx is None or debit_idx is None:
                        continue

                    for row in table[1:]:
                        try:
                            if not row[debit_idx] or row[debit_idx].strip() == "":
                                continue
                            amount = _parse_amount(row[debit_idx])
                            if amount == 0:
                                continue
                            date = _parse_date(row[date_idx])
                            if not date:
                                continue
                            results.append({
                                "merchant": row[desc_idx].strip(),
                                "amount": amount,
                                "currency": "INR",
                                "date": date,
                                "raw_text": row[desc_idx],
                            })
                        except (ValueError, IndexError, TypeError):
                            continue
    except Exception as e:
        print(f"PDF parsing error: {e}")

    return results
