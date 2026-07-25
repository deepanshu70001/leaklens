"""
Recurring subscription detector (§6).
Groups transactions by merchant, analyzes charge frequency, and classifies patterns.
"""
import statistics
from datetime import datetime
from typing import Optional
from app.config import settings


def detect_recurring(
    transactions: list[dict],
) -> list[dict]:
    """
    Given a list of transactions (sorted by merchant group), detect recurring patterns.

    Input: list of {merchant_normalized, amount, date, ...} dicts
    Output: list of detected subscriptions with frequency classification

    Returns list of:
    {
        "merchant_normalized": str,
        "frequency": "weekly" | "monthly" | "annual",
        "first_seen": datetime,
        "last_seen": datetime,
        "current_amount": float,
        "amounts": [float],           # all observed amounts for price-hike detection
        "dates": [datetime],          # all charge dates
        "transaction_count": int,
    }
    """
    from collections import defaultdict

    # Group by merchant
    merchant_groups: dict[str, list[dict]] = defaultdict(list)
    for txn in transactions:
        key = txn.get("merchant_normalized", "")
        if key:
            merchant_groups[key].append(txn)

    results = []

    for merchant, txns in merchant_groups.items():
        # Sort by date
        txns_sorted = sorted(txns, key=lambda t: t["date"])

        if len(txns_sorted) < settings.RECURRING_MIN_OCCURRENCES:
            # If there's only 1 transaction, check if it's explicitly an auto-pay setup
            is_explicit = any(t.get("is_explicit_setup", False) for t in txns_sorted)
            if not is_explicit:
                continue
            
            # For a single explicit setup message, we assume it's a monthly subscription
            amounts = [t["amount"] for t in txns_sorted]
            dates = [t["date"] for t in txns_sorted]
            results.append({
                "merchant_normalized": merchant,
                "frequency": "monthly", # Default assumed frequency
                "first_seen": dates[0],
                "last_seen": dates[-1],
                "current_amount": amounts[-1],
                "amounts": amounts,
                "dates": dates,
                "transaction_count": len(txns_sorted),
                "category": txns_sorted[0].get("category", "other"),
                "currency": txns_sorted[0].get("currency", "INR"),
            })
            continue

        # Compute inter-charge day gaps
        dates = [t["date"] for t in txns_sorted]
        gaps = []
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i - 1]).days
            if gap > 0:
                gaps.append(gap)

        if not gaps:
            continue

        mean_gap = statistics.mean(gaps)
        stdev_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0

        # Classify frequency based on mean gap with tolerance
        frequency = _classify_frequency(mean_gap, stdev_gap)

        if frequency is None:
            continue  # Gap pattern doesn't match any known frequency

        amounts = [t["amount"] for t in txns_sorted]

        results.append({
            "merchant_normalized": merchant,
            "frequency": frequency,
            "first_seen": dates[0],
            "last_seen": dates[-1],
            "current_amount": amounts[-1],
            "amounts": amounts,
            "dates": dates,
            "transaction_count": len(txns_sorted),
            "category": txns_sorted[0].get("category", "other"),
            "currency": txns_sorted[0].get("currency", "INR"),
        })

    return results


def _classify_frequency(mean_gap: float, stdev_gap: float) -> Optional[str]:
    """
    Classify frequency from mean inter-charge gap.
    Weekly: ~7 days (±tolerance scaled for weekly)
    Monthly: ~30 days (±tolerance)
    Annual: ~365 days (±tolerance scaled for annual)
    Semi-annual: ~180 days
    """
    tolerance = settings.RECURRING_GAP_TOLERANCE_DAYS

    # Weekly: 5-9 day mean gap, low stdev
    if 5 <= mean_gap <= 9 and stdev_gap <= tolerance:
        return "weekly"

    # Monthly: 25-35 day mean gap
    if 25 <= mean_gap <= 35 and stdev_gap <= tolerance * 3:
        return "monthly"

    # Semi-annual: 160-200 day mean gap
    if 160 <= mean_gap <= 200 and stdev_gap <= tolerance * 10:
        return "annual"  # Treat semi-annual as annual for simplicity

    # Annual: 340-395 day mean gap
    if 340 <= mean_gap <= 395 and stdev_gap <= tolerance * 15:
        return "annual"

    # Fallback: if we have enough occurrences and relatively consistent gaps
    if stdev_gap <= mean_gap * 0.3 and mean_gap < 400:
        if mean_gap < 14:
            return "weekly"
        elif mean_gap < 60:
            return "monthly"
        else:
            return "annual"

    return None
