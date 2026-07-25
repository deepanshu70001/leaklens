"""
Recommendation engine — wraps leak score with Groq reasoning (§6, §7).
"""
from app.services.leak_score import compute_leak_score, compute_days_since
from app.services.price_anomaly import get_max_price_increase_pct
from app.services.groq_client import generate_recommendation_reason
from app.config import CATEGORY_DISPLAY_NAMES


async def generate_full_recommendation(
    subscription: dict,
    all_subscriptions: list[dict],
) -> dict:
    """
    Compute leak score and generate recommendation with reasoning for a subscription.

    Returns:
    {
        "score": float,
        "components": dict,
        "recommendation": str,
        "reason": str,
    }
    """
    # Calculate days since last activity
    days_since = compute_days_since(subscription["last_seen"])

    # Get max price increase
    amounts = subscription.get("amounts", [subscription.get("current_amount", 0)])
    max_hike_pct = get_max_price_increase_pct(amounts)

    # Count other active subscriptions in the same category
    category = subscription.get("category", "other")
    others_in_category = sum(
        1 for s in all_subscriptions
        if s.get("category") == category
        and s.get("merchant_normalized") != subscription.get("merchant_normalized")
        and s.get("status", "active") == "active"
    )

    # Calculate category average amount
    category_amounts = [
        s.get("current_amount", 0) for s in all_subscriptions
        if s.get("category") == category and s.get("status", "active") == "active"
    ]
    category_avg = sum(category_amounts) / len(category_amounts) if category_amounts else 0

    # Compute leak score
    score_data = compute_leak_score(
        days_since_last_seen=days_since,
        max_price_increase_pct=max_hike_pct,
        other_active_in_category=others_in_category,
        amount=subscription.get("current_amount", 0),
        category_average_amount=category_avg,
    )

    # Find redundant services for the reasoning
    redundant_names = [
        s.get("merchant_normalized", "")
        for s in all_subscriptions
        if s.get("category") == category
        and s.get("merchant_normalized") != subscription.get("merchant_normalized")
        and s.get("status", "active") == "active"
    ]
    redundant_with = ", ".join(redundant_names[:3]) if redundant_names else "none"

    # Generate reasoning via Groq (with static fallback)
    reason = await generate_recommendation_reason(
        merchant=subscription.get("merchant_normalized", "Unknown"),
        recommendation=score_data["recommendation"],
        days_unused=days_since,
        price_increase_pct=max_hike_pct,
        redundant_with=redundant_with,
    )

    return {
        "score": score_data["score"],
        "components": score_data["components"],
        "recommendation": score_data["recommendation"],
        "reason": reason,
    }
