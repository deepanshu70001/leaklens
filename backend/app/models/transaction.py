"""
Transaction model — MongoDB transactions collection.
Stores individual parsed charges from SMS/email/statement.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    raw_text: str = ""
    merchant_raw: str = ""
    merchant_normalized: str = ""
    amount: float = 0.0
    currency: str = "INR"
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_type: str = "sms"  # "sms" | "email" | "statement"


class TransactionInDB(TransactionCreate):
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    merchant_raw: str
    merchant_normalized: str
    amount: float
    currency: str
    date: datetime
    source_type: str
