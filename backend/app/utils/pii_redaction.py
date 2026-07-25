"""
PII Redaction — mask sensitive data before any LLM call (§9).
- Card/account numbers → last 4 digits only
- Phone numbers → last 4 digits only
- OTP patterns → stripped entirely
"""
import re


def redact_pii(text: str) -> str:
    """Apply all PII redaction rules to a string before external transmission."""
    if not text:
        return text

    result = text

    # 1. Strip OTP patterns entirely (e.g., "OTP 123456", "OTP: 4567", "otp is 789012")
    result = re.sub(
        r'\b[Oo][Tt][Pp]\s*[:\-]?\s*\d{4,8}\b',
        '[OTP_REDACTED]',
        result
    )

    # 2. Mask card numbers (16 digits with optional separators)
    # Matches: 1234-5678-9012-3456, 1234 5678 9012 3456, 1234567890123456
    result = re.sub(
        r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?)(\d{4})\b',
        r'XXXX-XXXX-XXXX-\2',
        result
    )

    # 3. Mask account numbers (formats like XX4521, XXXX1234, a/c 12345678)
    # Keep the masked format as-is if already masked (XX4521)
    result = re.sub(
        r'\ba/c\s+(\d{4,}?)(\d{4})\b',
        r'a/c XXXX\2',
        result
    )

    # 4. Mask full phone numbers (10+ digit Indian/international numbers)
    # Keep last 4 digits
    result = re.sub(
        r'\b(\+?\d{1,3}[\s\-]?)?\(?\d{3,5}\)?[\s\-]?\d{3,4}[\s\-]?(\d{4})\b',
        lambda m: f'XXXXX-{m.group(2)}' if len(re.sub(r'[\s\-\(\)\+]', '', m.group(0))) >= 10 else m.group(0),
        result
    )

    # 5. Mask email addresses (keep domain for context)
    result = re.sub(
        r'\b[a-zA-Z0-9._%+\-]+@([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b',
        r'[EMAIL]@\1',
        result
    )

    return result


def mask_account_number(account: str) -> str:
    """Mask an account number to show only last 4 digits."""
    if not account or len(account) < 4:
        return account
    return "X" * (len(account) - 4) + account[-4:]


def mask_phone_number(phone: str) -> str:
    """Mask a phone number to show only last 4 digits."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) < 4:
        return phone
    return "X" * (len(digits) - 4) + digits[-4:]
