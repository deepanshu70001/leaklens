"""
Leak Score engine (§6) — combines usage, price hike, redundancy, and relative cost signals.
"""
from datetime import datetime, timezone
from app.config import settings, LEAK_SCORE_WEIGHTS, LEAK_SCORE_BANDS


def compute_leak_score(
    days_since_last_seen: int,
    max_price_increase_pct: float,
    other_active_in_category: int,
    amount: float,
    category_average_amount: float,
) -> dict:
    """
    Compute the Leak Score (0-100, higher = worse leak).

    Returns:
    {
        "score": float,
        "components": {
            "unused": float,
            "price_hike": float,
            "redundancy": float,
            "relative_cost": float,
        },
        "recommendation": str,
    }
    """
    # Component calculations per §6 formula
    unused_score = min(days_since_last_seen / settings.UNUSED_DAYS_CAP, 1.0)
    price_hike_score = min(max_price_increase_pct / 50.0, 1.0)
    redundancy_score = 1.0 if other_active_in_category > 1 else 0.0

    # Avoid division by zero
    if category_average_amount > 0:
        relative_cost_score = min(amount / category_average_amount, 1.0)
    else:
        relative_cost_score = 0.5  # Neutral if no comparison data

    # Weighted total
    score = 100 * (
        LEAK_SCORE_WEIGHTS["unused"] * unused_score
        + LEAK_SCORE_WEIGHTS["price_hike"] * price_hike_score
        + LEAK_SCORE_WEIGHTS["redundancy"] * redundancy_score
        + LEAK_SCORE_WEIGHTS["relative_cost"] * relative_cost_score
    )

    score = round(min(max(score, 0), 100), 1)

    # Map to recommendation band
    recommendation = _score_to_recommendation(score)

    return {
        "score": score,
        "components": {
            "unused": round(unused_score * 100, 1),
            "price_hike": round(price_hike_score * 100, 1),
            "redundancy": round(redundancy_score * 100, 1),
            "relative_cost": round(relative_cost_score * 100, 1),
        },
        "recommendation": recommendation,
    }


def _score_to_recommendation(score: float) -> str:
    """Map a leak score to a recommendation band."""
    for recommendation, (low, high) in LEAK_SCORE_BANDS.items():
        if low <= score <= high:
            return recommendation
    # Default fallback
    if score > 75:
        return "cancel"
    return "keep"


def compute_days_since(last_seen: datetime) -> int:
    """Compute days between now and the last seen date."""
    now = datetime.now(timezone.utc)
    if last_seen.tzinfo is None:
        from datetime import timezone as tz
        last_seen = last_seen.replace(tzinfo=tz.utc)
    delta = now - last_seen
    return max(delta.days, 0)
