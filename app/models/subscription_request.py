from typing import Optional

from pydantic import BaseModel


class SubscriptionRequest(BaseModel):
    tier: int
    billing_type: str
    coupon: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    session_id: str
