"""
Merchant normalization — cleanup + rapidfuzz grouping (§6).
"""
import re
from rapidfuzz import fuzz
from app.config import settings, CATEGORY_MAP


# Prefixes and suffixes to strip from merchant names
STRIP_PREFIXES = [
    "PAYPAL *", "PAYPAL*", "PAYPAL ", "*RECUR", "UPI/",
    "GOOGLE *", "APPLE.COM/BILL ", "AMZN ", "AMZ*",
]

STRIP_SUFFIXES = [
    " SUBSCRIPTION", " PREMIUM", " MEMBERSHIP", " RECUR",
    " INDIA", " IND", " PAYMENT", " BILL",
]

# Regex to strip trailing transaction IDs / reference numbers
TXNID_PATTERN = re.compile(r'[\s\-]*(?:Ref#?|TXN|ID|#)\s*[\w\d]+$', re.IGNORECASE)
TRAILING_NUMBERS = re.compile(r'[\s\-\*]+\d{3,}$')


def normalize_merchant(raw_merchant: str) -> str:
    """
    Clean up a raw merchant name:
    1. Lowercase
    2. Strip payment-processor prefixes
    3. Strip trailing transaction IDs
    4. Collapse whitespace
    """
    if not raw_merchant:
        return ""

    name = raw_merchant.strip()

    # Remove prefixes
    for prefix in STRIP_PREFIXES:
        if name.upper().startswith(prefix.upper()):
            name = name[len(prefix):]

    # Remove suffixes
    for suffix in STRIP_SUFFIXES:
        if name.upper().endswith(suffix.upper()):
            name = name[:-len(suffix)]

    # Strip trailing transaction IDs
    name = TXNID_PATTERN.sub('', name)
    name = TRAILING_NUMBERS.sub('', name)

    # Lowercase and collapse whitespace
    name = re.sub(r'\s+', ' ', name.lower()).strip()

    # Remove special characters like * at beginning
    name = name.lstrip('*').strip()

    return name


def group_merchants(merchant_names: list[str]) -> dict[str, str]:
    """
    Group similar merchant names using fuzzy matching.
    Returns a mapping of {raw_normalized -> canonical_name}.
    The canonical name is the most common variant.
    """
    if not merchant_names:
        return {}

    # Count occurrences of each normalized name
    from collections import Counter
    counts = Counter(merchant_names)

    # Sort by frequency (most common first — becomes canonical)
    sorted_names = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)

    # Build mapping
    canonical_map: dict[str, str] = {}
    used_canonical: list[str] = []

    for name in sorted_names:
        if name in canonical_map:
            continue

        # Check against existing canonical names
        matched = False
        for canonical in used_canonical:
            score = fuzz.ratio(name, canonical)
            if score >= settings.FUZZY_MATCH_THRESHOLD:
                canonical_map[name] = canonical
                matched = True
                break

        if not matched:
            canonical_map[name] = name
            used_canonical.append(name)

    return canonical_map


def categorize_merchant(normalized_name: str) -> str:
    """
    Assign a category to a merchant based on known mappings.
    Falls back to 'other' for unrecognized merchants.
    """
    name_lower = normalized_name.lower()

    for keyword, category in CATEGORY_MAP.items():
        if keyword in name_lower:
            return category

    return "other"
