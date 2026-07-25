"""
Price anomaly detection — flag silent price hikes (§6).
"""
from app.config import settings


def detect_price_hikes(amounts: list[float]) -> list[dict]:
    """
    Compare sequential charges and flag increases above the threshold.

    Returns list of:
    {
        "from_amount": float,
        "to_amount": float,
        "increase_pct": float,
        "index": int,  # index of the hike in the amounts list
    }
    """
    hikes = []

    for i in range(1, len(amounts)):
        prev = amounts[i - 1]
        curr = amounts[i]

        if prev > 0 and curr > prev:
            pct_increase = ((curr - prev) / prev) * 100
            if pct_increase >= settings.PRICE_HIKE_THRESHOLD_PCT:
                hikes.append({
                    "from_amount": prev,
                    "to_amount": curr,
                    "increase_pct": round(pct_increase, 1),
                    "index": i,
                })

    return hikes


def get_max_price_increase_pct(amounts: list[float]) -> float:
    """Get the maximum percentage increase across all sequential charges."""
    hikes = detect_price_hikes(amounts)
    if not hikes:
        return 0.0
    return max(h["increase_pct"] for h in hikes)


def build_price_history(amounts: list[float], dates: list) -> list[dict]:
    """
    Build price history entries from parallel amounts and dates lists.
    Only records entries where the price changed.
    """
    history = []
    last_amount = None

    for i, (amount, date) in enumerate(zip(amounts, dates)):
        if amount != last_amount:
            history.append({
                "amount": amount,
                "effective_date": date,
            })
            last_amount = amount

    # Always include the first and last even if no change
    if history and len(amounts) > 0:
        if history[0]["amount"] != amounts[0]:
            history.insert(0, {"amount": amounts[0], "effective_date": dates[0]})

    return history
