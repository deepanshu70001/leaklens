from fastapi import APIRouter, Depends, HTTPException, Form, Request
from pydantic import BaseModel
from app.config import settings
from app.database import get_db
from twilio.rest import Client
import logging

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

class TriggerRequest(BaseModel):
    subscription_id: str

@router.post("/trigger")
async def trigger_whatsapp(request: TriggerRequest, db = Depends(get_db)):
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise HTTPException(status_code=500, detail="Twilio credentials not configured.")
        
    sub = await db["subscriptions"].find_one({"id": request.subscription_id})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    amount = sub.get("current_amount", 0)
    merchant = sub.get("merchant_normalized", "Service").title()
    
    message_body = (
        f"Hey! LeakLens noticed you paid ₹{amount:,} for {merchant} but haven't used it much recently.\n\n"
        f"Reply CANCEL and I will email their support to close the account."
    )
    
    try:
        message = client.messages.create(
            from_=settings.TWILIO_FROM_NUMBER,
            body=message_body,
            to=settings.TWILIO_TO_NUMBER
        )
        # Store context in DB for the webhook to know which sub we're talking about
        await db["whatsapp_state"].update_one(
            {"user_phone": settings.TWILIO_TO_NUMBER},
            {"$set": {"active_subscription_id": request.subscription_id}},
            upsert=True
        )
        return {"status": "success", "message_sid": message.sid}
    except Exception as e:
        logging.error(f"Failed to send Twilio message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def whatsapp_webhook(request: Request, db = Depends(get_db)):
    # Twilio sends data as Form URL-encoded
    form_data = await request.form()
    incoming_msg = form_data.get("Body", "").strip().lower()
    sender = form_data.get("From", "")
    
    if incoming_msg == "cancel":
        # Find active subscription context
        state = await db["whatsapp_state"].find_one({"user_phone": sender})
        if not state or not state.get("active_subscription_id"):
            return "No active subscription found to cancel."
            
        sub_id = state["active_subscription_id"]
        sub = await db["subscriptions"].find_one({"id": sub_id})
        
        if sub:
            # Trigger ghost cancel internally
            try:
                await db["subscriptions"].update_one(
                    {"id": sub_id},
                    {"$set": {"status": "canceled"}}
                )
                
                amount = sub.get("current_amount", 0)
                merchant = sub.get("merchant_normalized", "Service").title()
                
                response_msg = f"✅ Done! I've dispatched the ghost cancellation email to {merchant} Support. You just saved ₹{amount:,}/mo!"
                
                # Clear state
                await db["whatsapp_state"].delete_one({"user_phone": sender})
                
            except Exception as e:
                response_msg = f"❌ Oops, failed to send cancellation email."
        else:
            response_msg = "Could not find that subscription in database."
            
        # Send reply
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=settings.TWILIO_FROM_NUMBER,
            body=response_msg,
            to=sender
        )
        return {"status": "processed"}
    
    return {"status": "ignored"}
