from typing import Any

import stripe

from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_checkout_session(
    line_items: list, success_url: str, cancel_url: str, metadata: dict = None, discounts: list = None
) -> Any:
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
        discounts=discounts,
        billing_address_collection="required",
    )
    return session


async def get_checkout_session(session_id: str) -> Any:
    session = stripe.checkout.Session.retrieve(session_id)
    return session


async def verify_webhook(payload: bytes, sig_header: str) -> Any:
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        return event
    except Exception as e:
        raise e
