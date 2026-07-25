"""
Dashboard router — /api/dashboard/summary (§5).
Aggregate stats: total monthly leak, category breakdown, recommendation bands.
"""
from fastapi import APIRouter, Depends
from bson import ObjectId
from collections import defaultdict
from app.database import get_database
from app.auth import get_current_user
from app.config import CATEGORY_DISPLAY_NAMES

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """
    Aggregate dashboard data:
    - Total monthly leak amount
    - Category breakdown (amounts + counts)
    - Count by recommendation band
    - Aggregate leak score
    """
    user_id = ObjectId(str(current_user["_id"]))

    # Get all active subscriptions
    subscriptions = []
    async for sub in db.subscriptions.find({"user_id": user_id, "status": "active"}):
        score_data = await db.leak_scores.find_one(
            {"subscription_id": sub["_id"]},
            sort=[("computed_at", -1)],
        )
        subscriptions.append({
            **sub,
            "_score_data": score_data,
        })

    # Total monthly leak (normalize annual to monthly)
    total_monthly = 0.0
    for sub in subscriptions:
        amount = sub.get("current_amount", 0)
        freq = sub.get("frequency", "monthly")
        if freq == "annual":
            total_monthly += amount / 12
        elif freq == "weekly":
            total_monthly += amount * 4.33
        else:
            total_monthly += amount

    # Category breakdown
    category_breakdown = defaultdict(lambda: {"amount": 0.0, "count": 0, "display_name": ""})
    for sub in subscriptions:
        cat = sub.get("category", "other")
        amount = sub.get("current_amount", 0)
        freq = sub.get("frequency", "monthly")
        if freq == "annual":
            monthly_amount = amount / 12
        elif freq == "weekly":
            monthly_amount = amount * 4.33
        else:
            monthly_amount = amount
        category_breakdown[cat]["amount"] += monthly_amount
        category_breakdown[cat]["count"] += 1
        category_breakdown[cat]["display_name"] = CATEGORY_DISPLAY_NAMES.get(cat, "Other")

    # Recommendation band counts
    band_counts = {"keep": 0, "downgrade": 0, "renegotiate": 0, "cancel": 0}
    total_score = 0.0
    scored_count = 0

    for sub in subscriptions:
        score_data = sub.get("_score_data")
        if score_data:
            rec = score_data.get("recommendation", "keep")
            band_counts[rec] = band_counts.get(rec, 0) + 1
            total_score += score_data.get("score", 0)
            scored_count += 1

    avg_score = round(total_score / scored_count, 1) if scored_count > 0 else 0.0

    # Total potential savings (from subscriptions recommended for cancel/downgrade)
    potential_savings = 0.0
    for sub in subscriptions:
        score_data = sub.get("_score_data")
        if score_data and score_data.get("recommendation") in ("cancel", "downgrade"):
            amount = sub.get("current_amount", 0)
            freq = sub.get("frequency", "monthly")
            if freq == "annual":
                potential_savings += amount / 12
            elif freq == "weekly":
                potential_savings += amount * 4.33
            else:
                potential_savings += amount

    # Already recovered (from actions)
    total_recovered = 0.0
    async for action in db.actions.find({"user_id": user_id}):
        total_recovered += action.get("money_recovered", 0)

    return {
        "total_monthly_spend": round(total_monthly, 2),
        "total_subscriptions": len(subscriptions),
        "average_leak_score": avg_score,
        "potential_monthly_savings": round(potential_savings, 2),
        "total_recovered": round(total_recovered, 2),
        "category_breakdown": [
            {
                "category": cat,
                "display_name": data["display_name"],
                "monthly_amount": round(data["amount"], 2),
                "count": data["count"],
            }
            for cat, data in sorted(category_breakdown.items(), key=lambda x: x[1]["amount"], reverse=True)
        ],
        "recommendation_counts": band_counts,
    }
