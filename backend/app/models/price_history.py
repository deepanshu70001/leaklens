"""
Price history model — MongoDB price_history collection.
Tracks every observed price point for a subscription.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class PriceHistoryEntry(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    subscription_id: Optional[str] = None
    amount: float = 0.0
    effective_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PriceHistoryResponse(BaseModel):
    amount: float
    effective_date: datetime
