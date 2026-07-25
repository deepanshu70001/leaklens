"""
Subscription model — MongoDB subscriptions collection.
Represents a detected recurring charge group.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class SubscriptionInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = None
    merchant_normalized: str = ""
    category: str = "other"
    frequency: str = "monthly"  # "weekly" | "monthly" | "annual"
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_amount: float = 0.0
    currency: str = "INR"
    status: str = "active"  # "active" | "canceled" | "downgraded"


class SubscriptionResponse(BaseModel):
    id: str
    merchant_normalized: str
    category: str
    category_display: str = ""
    frequency: str
    first_seen: datetime
    last_seen: datetime
    current_amount: float
    currency: str
    status: str
    # Joined from leak_scores
    leak_score: Optional[float] = None
    recommendation: Optional[str] = None
    reason: Optional[str] = None
    score_components: Optional[dict] = None
    # Joined from price_history
    price_history: Optional[list] = None
    price_hike_detected: bool = False
    price_hike_pct: Optional[float] = None


class SubscriptionListResponse(BaseModel):
    subscriptions: list[SubscriptionResponse]
    total: int
