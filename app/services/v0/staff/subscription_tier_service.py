import json

import stripe

from app.core.config import settings
from app.models.staff.subscription_tier import (
    SubscriptionTierIn,
    SubscriptionTierOut,
    SubscriptionTierUpdate,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


async def get_subscription_tiers(redis):
    cache_key = "subscription_tier"
    await redis.delete("subscription_tier")

    cached_data = await redis.get(cache_key)
    if cached_data:
        return cached_data
    else:
        tiers = await SubscriptionTierOut.get_tiers()
        serializable_result = [
            {**tier.model_dump(), "created_at": str(tier.created_at), "updated_at": str(tier.updated_at)}
            for tier in tiers
        ]
        await redis.set(cache_key, json.dumps(serializable_result), ex=86400)
        return tiers


# create product then pass it to subscription price
async def create_subscription_product(redis, tier: str, description: str):
    product = stripe.Product.create(name=tier, description=description)
    await redis.delete("subscription_tier")
    return product


async def create_subscription_price(product, unit_amount: int, currency="INR", interval="month"):
    try:
        # unit_amount should be specified in the smallest currency unit (e.g. paise for INR)
        price = stripe.Price.create(
            unit_amount=unit_amount,
            currency=currency,
            recurring={"interval": interval},
            product=product.id,
        )
        await SubscriptionTierIn.create_tier(
            product.id, product.name, product.description, price.id, unit_amount, None, None, currency
        )
        return price
    except Exception as e:
        raise ValueError(str(e))


async def delete_subscription_product(redis, product_id):
    stripe.Product.modify(product_id, active=False)
    await redis.delete("subscription_tier")
    return await SubscriptionTierUpdate.delete_tier(product_id)


async def activate_subscription_product(redis, product_id):
    stripe.Product.modify(product_id, active=True)
    await redis.delete("subscription_tier")
    return await SubscriptionTierUpdate.activate_tier(product_id)


async def update_subscription_tier(redis, tier_id: int, tier: SubscriptionTierUpdate):
    await redis.delete("subscription_tier")
    res = await SubscriptionTierOut.get_tier_by_id(tier_id)
    if tier.name is not None or tier.description is not None:
        stripe.Product.modify(
            res.stripe_product_id,
            **{k: v for k, v in {"name": tier.name, "description": tier.description}.items() if v is not None},
        )

    if tier.amount is not None:
        stripe.Price.modify(res.stripe_price_id, active=False)
        new_price = stripe.Price.create(
            unit_amount=tier.amount,
            currency=tier.currency if tier.currency else "INR",
            recurring={"interval": "month"},
            product=res.stripe_product_id,
        )
        return await SubscriptionTierUpdate.update_tier(
            tier_id,
            tier.name,
            tier.description,
            tier.amount,
            tier.stripe_coupon_id,
            tier.discount_amount,
            tier.currency,
            new_price.id,
        )
    return await SubscriptionTierUpdate.update_tier(
        tier_id, tier.name, tier.description, tier.amount, tier.stripe_coupon_id, tier.discount_amount, tier.currency
    )
