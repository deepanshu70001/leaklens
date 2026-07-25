"""
Actions router — /api/subscriptions/{id}/action (§5).
Records user actions on recommendations, computes money recovered.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.database import get_database
from app.auth import get_current_user
from app.models.action import ActionCreate, ActionResponse

router = APIRouter(prefix="/api/subscriptions", tags=["actions"])


@router.post("/{subscription_id}/action")
async def take_action(
    subscription_id: str,
    action_data: ActionCreate,
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """
    Record a user action on a subscription.
    If action is cancel/downgrade, compute money_recovered and optionally redirect to growth.
    """
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

    valid_actions = {"keep", "cancel", "downgrade", "renegotiate"}
    if action_data.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

    # Compute money recovered
    money_recovered = 0.0
    current_amount = sub.get("current_amount", 0)
    frequency = sub.get("frequency", "monthly")

    # Normalize to monthly amount
    if frequency == "annual":
        monthly_amount = current_amount / 12
    elif frequency == "weekly":
        monthly_amount = current_amount * 4.33
    else:
        monthly_amount = current_amount

    if action_data.action == "cancel":
        money_recovered = monthly_amount  # Full monthly amount recovered
    elif action_data.action == "downgrade":
        money_recovered = monthly_amount * 0.5  # Assume 50% savings on downgrade

    # Update subscription status
    new_status = sub.get("status", "active")
    if action_data.action == "cancel":
        new_status = "canceled"
    elif action_data.action == "downgrade":
        new_status = "downgraded"

    await db.subscriptions.update_one(
        {"_id": sub["_id"]},
        {"$set": {"status": new_status}},
    )

    # Record the action
    action_doc = {
        "subscription_id": sub["_id"],
        "user_id": user_id,
        "action_taken": action_data.action,
        "money_recovered": round(money_recovered, 2),
        "redirected_to_growth": action_data.redirected_to_growth if money_recovered > 0 else False,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.actions.insert_one(action_doc)

    return {
        "id": str(result.inserted_id),
        "subscription_id": subscription_id,
        "action_taken": action_data.action,
        "money_recovered": round(money_recovered, 2),
        "redirected_to_growth": action_doc["redirected_to_growth"],
        "new_status": new_status,
        "created_at": action_doc["created_at"],
        "message": _action_message(action_data.action, sub.get("merchant_normalized", ""), money_recovered),
    }


def _action_message(action: str, merchant: str, money_recovered: float) -> str:
    """Generate a user-friendly action confirmation message."""
    if action == "cancel":
        return f"Marked {merchant} for cancellation. ₹{money_recovered:.0f}/month can now be redirected to your growth fund."
    elif action == "downgrade":
        return f"Marked {merchant} for downgrade. Estimated ₹{money_recovered:.0f}/month in savings."
    elif action == "renegotiate":
        return f"Marked {merchant} for renegotiation. Use the negotiation script to contact their support team."
    else:
        return f"Keeping {merchant}. Good choice if it provides value."
