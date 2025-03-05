import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.subscription_request import CheckoutSessionResponse, SubscriptionRequest
from app.models.user import UserModel
from app.services.v0 import payment_gateway
from app.services.v0.subscription_request import (
    get_subscription_plan_and_price,
    insert_user_subscription,
    insert_webhook_response,
)

router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
log = logging.getLogger("fastapi")


@protected_router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request_data: SubscriptionRequest,
    current_user: UserModel = Depends(get_current_user),
):
    plan = await get_subscription_plan_and_price(request_data.tier, request_data.billing_type)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid subscription tier or billing type")

    line_items = [{"price": plan["stripe_price_id"], "quantity": 1}]

    # For annual billing, apply a discount coupon if available.
    discounts = None
    if request_data.billing_type.lower() == "annual":
        if not plan["stripe_coupon_id"]:
            raise HTTPException(status_code=400, detail="Annual discount is not configured for this plan")
        discounts = [{"coupon": plan["stripe_coupon_id"]}]

    # Metadata to use in webhooks
    metadata = {"user_id": current_user["id"], "tier": request_data.tier, "billing_type": request_data.billing_type}

    try:
        session = await payment_gateway.create_checkout_session(
            line_items=line_items,
            success_url=f"{settings.FRONTEND_URL}/success?session_id=" + "{CHECKOUT_SESSION_ID}",
            cancel_url=f"{settings.FRONTEND_URL}/cancel",
            metadata=metadata,
            discounts=discounts,
        )
        return CheckoutSessionResponse(session_id=session.id)
    except Exception as e:
        log.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session-success/{session_id}")
async def session_success(session_id: str):
    try:
        session = await payment_gateway.get_checkout_session(session_id)
        return session
    except Exception as e:
        log.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = await payment_gateway.verify_webhook(payload, sig_header)
    except Exception as e:
        log.error(e)
        return Response(content=str(e), status_code=400)

    await insert_webhook_response(event["id"], event["type"], event)
    # Process webhook events from Stripe.
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        tier = metadata.get("tier")
        billing_type = metadata.get("billing_type")
        stripe_subscription_id = session.get("subscription")
        await insert_user_subscription(user_id, int(tier), billing_type, stripe_subscription_id)
    elif event["type"] == "invoice.paid":
        pass

    return Response(status_code=200)
