"""
Negotiate router — /api/negotiate/{id} (§5, §7).
Generates Groq-powered cancellation/negotiation message drafts.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from bson import ObjectId
from app.database import get_database
from app.auth import get_current_user
from app.services.groq_client import generate_negotiation_script
from app.main import limiter

router = APIRouter(prefix="/api/negotiate", tags=["negotiate"])


@router.post("/{subscription_id}")
@limiter.limit("10/minute")
async def generate_negotiation_message(
    request: Request,
    subscription_id: str,
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """
    Generate a polite cancellation/negotiation message for a subscription.
    Uses Groq with a static fallback if unavailable.
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

    # Get the leak score for reasoning context
    score_data = await db.leak_scores.find_one(
        {"subscription_id": sub["_id"]},
        sort=[("computed_at", -1)],
    )

    recommendation = score_data.get("recommendation", "cancel") if score_data else "cancel"
    reason = score_data.get("reason", "Looking for a better deal") if score_data else "Looking for a better deal"

    # Calculate tenure
    first_seen = sub.get("first_seen", datetime.now(timezone.utc))
    months_subscribed = max(1, (datetime.now(timezone.utc) - first_seen.replace(tzinfo=timezone.utc) if first_seen.tzinfo is None else first_seen).days // 30)

    action = "renegotiate" if recommendation in ("renegotiate", "downgrade") else "cancel"

    message = await generate_negotiation_script(
        merchant=sub.get("merchant_normalized", "the service"),
        action=action,
        amount=sub.get("current_amount", 0),
        tenure_months=months_subscribed,
        reason=reason,
    )

    return {
        "subscription_id": subscription_id,
        "merchant": sub.get("merchant_normalized", ""),
        "action": action,
        "message": message,
        "note": "This is a suggested message draft. Feel free to personalize it before sending.",
    }
