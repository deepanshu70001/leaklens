"""
Subscriptions router — /api/subscriptions (§5).
"""
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.database import get_database
from app.auth import get_current_user
from app.config import CATEGORY_DISPLAY_NAMES
from app.services.price_anomaly import get_max_price_increase_pct

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


def _format_subscription(sub: dict, score_data: dict = None, price_history: list = None) -> dict:
    """Format a subscription document for API response."""
    category = sub.get("category", "other")

    result = {
        "id": str(sub["_id"]),
        "merchant_normalized": sub.get("merchant_normalized", ""),
        "category": category,
        "category_display": CATEGORY_DISPLAY_NAMES.get(category, "Other"),
        "frequency": sub.get("frequency", "monthly"),
        "first_seen": sub.get("first_seen"),
        "last_seen": sub.get("last_seen"),
        "current_amount": sub.get("current_amount", 0),
        "currency": sub.get("currency", "INR"),
        "status": sub.get("status", "active"),
        "leak_score": None,
        "recommendation": None,
        "reason": None,
        "score_components": None,
        "price_history": [],
        "price_hike_detected": False,
        "price_hike_pct": None,
    }

    if score_data:
        result["leak_score"] = score_data.get("score")
        result["recommendation"] = score_data.get("recommendation")
        result["reason"] = score_data.get("reason")
        result["score_components"] = score_data.get("components")

    if price_history:
        result["price_history"] = [
            {"amount": ph["amount"], "effective_date": ph["effective_date"]}
            for ph in price_history
        ]
        amounts = [ph["amount"] for ph in price_history]
        max_hike = get_max_price_increase_pct(amounts)
        if max_hike > 0:
            result["price_hike_detected"] = True
            result["price_hike_pct"] = max_hike

    return result


@router.get("")
async def list_subscriptions(
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """List all subscriptions with current leak score and recommendation."""
    user_id = ObjectId(str(current_user["_id"]))

    subscriptions = []
    async for sub in db.subscriptions.find({"user_id": user_id}).sort("current_amount", -1):
        # Get leak score
        score_data = await db.leak_scores.find_one(
            {"subscription_id": sub["_id"]},
            sort=[("computed_at", -1)],
        )

        # Get price history
        price_history = []
        async for ph in db.price_history.find({"subscription_id": sub["_id"]}).sort("effective_date", 1):
            price_history.append(ph)

        subscriptions.append(_format_subscription(sub, score_data, price_history))

    return {"subscriptions": subscriptions, "total": len(subscriptions)}


@router.get("/{subscription_id}")
async def get_subscription_detail(
    subscription_id: str,
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """Get full subscription detail: price history, reasoning, usage signal."""
    user_id = ObjectId(str(current_user["_id"]))

    try:
        sub = await db.subscriptions.find_one({
            "_id": ObjectId(subscription_id),
            "user_id": user_id,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid subscription ID")

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Get leak score
    score_data = await db.leak_scores.find_one(
        {"subscription_id": sub["_id"]},
        sort=[("computed_at", -1)],
    )

    # Get full price history
    price_history = []
    async for ph in db.price_history.find({"subscription_id": sub["_id"]}).sort("effective_date", 1):
        price_history.append(ph)

    # Get related transactions
    transactions = []
    async for txn in db.transactions.find({
        "user_id": user_id,
        "merchant_normalized": sub.get("merchant_normalized"),
    }).sort("date", -1).limit(20):
        transactions.append({
            "id": str(txn["_id"]),
            "amount": txn["amount"],
            "date": txn["date"],
            "merchant_raw": txn.get("merchant_raw", ""),
        })

    # Get actions taken
    actions = []
    async for action in db.actions.find({"subscription_id": sub["_id"]}).sort("created_at", -1):
        actions.append({
            "id": str(action["_id"]),
            "action_taken": action["action_taken"],
            "money_recovered": action.get("money_recovered", 0),
            "redirected_to_growth": action.get("redirected_to_growth", False),
            "created_at": action["created_at"],
        })

    result = _format_subscription(sub, score_data, price_history)
    result["transactions"] = transactions
    result["actions"] = actions

    return result
