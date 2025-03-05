from datetime import datetime
from typing import Optional

from app.core.database import DataBase


class SubscriptionTierIn(DataBase):
    stripe_product_id: str
    name: str
    description: str
    price: int
    currency: str

    @classmethod
    async def create_tier(
        cls,
        stripe_product_id: str,
        name: str,
        description: str,
        stripe_price_id: str,
        price: int,
        stripe_coupon_id: str = None,
        discount_amount: int = None,
        currency: str = "INR",
    ):
        query = """
           WITH updated_tier AS (
                UPDATE subscription_tiers
                   SET name = COALESCE($1, name),
                       description = COALESCE($2, description),
                       updated_at = NOW()
                 WHERE id = $7
             RETURNING *
            )
         UPDATE subscription_prices
            SET stripe_coupon_id = COALESCE($3, stripe_coupon_id),
                amount = COALESCE($4, amount),
                discount_amount = COALESCE($5, discount_amount),
                currency = COALESCE($6, currency),
                updated_at = NOW()
          WHERE subscription_tier_id = (SELECT updated_tier.id FROM updated_tier)
            AND billing_type = 'monthly'
      RETURNING updated_tier.*, subscription_prices.*;
        """
        await cls.execute(
            query,
            name,
            description,
            stripe_product_id,
            stripe_price_id,
            stripe_coupon_id,
            price,
            discount_amount,
            currency,
        )
        return True


class SubscriptionTierOut(DataBase):
    id: int
    name: str
    description: str
    stripe_price_id: str
    stripe_product_id: str
    stripe_coupon_id: Optional[str] = None
    amount: int
    discount_amount: Optional[int] = None
    currency: str
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @classmethod
    async def get_tiers(cls):
        query = """
            SELECT st.id, st.name, st.description, st.deleted_at, st.created_at, st.updated_at,
                   sp.amount, sp.stripe_price_id, sp.stripe_product_id, sp.stripe_coupon_id,
                   sp.discount_amount, sp.currency
              FROM subscription_tiers st
             JOIN subscription_prices sp ON st.id = sp.subscription_tier_id
            """
        return await cls.fetch(query)

    @classmethod
    async def get_tier_by_id(cls, tier_id: int):
        query = """
              SELECT st.id, st.name, st.description, st.deleted_at, st.created_at, st.updated_at,
                     sp.amount, sp.stripe_price_id, sp.stripe_product_id, sp.stripe_coupon_id,
                     sp.discount_amount, sp.currency
                FROM subscription_tiers st
                JOIN subscription_prices sp ON st.id = sp.subscription_tier_id
               WHERE st.id = $1
                    """
        return await cls.fetchrow(query, tier_id)


class SubscriptionTierUpdate(DataBase):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    stripe_coupon_id: Optional[str] = None
    discount_amount: Optional[int] = None

    @classmethod
    async def delete_tier(cls, stripe_product_id: str):
        query = """
           UPDATE subscription_tiers SET deleted_at = NOW()
            WHERE id = (
                        SELECT subscription_tier_id FROM subscription_prices WHERE stripe_product_id = $1
                        )
            """
        return await cls.execute(query, stripe_product_id)

    @classmethod
    async def activate_tier(cls, stripe_product_id: str):
        query = """
               UPDATE subscription_tiers SET deleted_at = NULL
                WHERE id = (
                            SELECT subscription_tier_id FROM subscription_prices WHERE stripe_product_id = $1
                            )
                """
        return await cls.execute(query, stripe_product_id)

    @classmethod
    async def update_tier(
        cls,
        tier_id: int,
        name: str,
        description: str,
        price: int,
        stripe_coupon_id: str = None,
        discount_amount: int = None,
        currency: str = "INR",
        stripe_price_id: str = None,
    ):
        query = """
            WITH updated_tier AS (
          UPDATE subscription_tiers
             SET name = COALESCE($1, name),
                 description = COALESCE($2, description),
                 updated_at = NOW()
           WHERE id = $7
       RETURNING id, name, description
        )
          UPDATE subscription_prices sp
             SET stripe_coupon_id = COALESCE($3, sp.stripe_coupon_id),
                 amount = COALESCE($4, sp.amount),
                 discount_amount = COALESCE($5, sp.discount_amount),
                 currency = COALESCE($6, sp.currency),
                 stripe_price_id = COALESCE($8, sp.stripe_price_id),
                 updated_at = NOW()
            FROM updated_tier ut
           WHERE sp.subscription_tier_id = ut.id  AND sp.billing_type = 'monthly'
       RETURNING sp.*, ut.name, ut.description;
            """
        return await cls.fetch(
            query, name, description, stripe_coupon_id, price, discount_amount, currency, tier_id, stripe_price_id
        )
