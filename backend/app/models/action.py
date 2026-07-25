"""
Action model — MongoDB actions collection.
Records user actions on subscription recommendations.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ActionCreate(BaseModel):
    action: str  # "keep" | "cancel" | "downgrade" | "renegotiate"
    redirected_to_growth: bool = True


class ActionInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    subscription_id: Optional[str] = None
    user_id: Optional[str] = None
    action_taken: str = ""
    money_recovered: float = 0.0
    redirected_to_growth: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActionResponse(BaseModel):
    id: str
    subscription_id: str
    action_taken: str
    money_recovered: float
    redirected_to_growth: bool
    created_at: datetime
