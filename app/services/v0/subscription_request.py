import datetime

from app.core.database import DataBase


# Retrieve the subscription tier and pricing details from the database.
async def get_subscription_plan_and_price(tier: int, billing_type: str):
    query = """
      SELECT st.id as tier_id, st.name, st.description,
               sp.id as price_id, sp.billing_type, sp.stripe_price_id, sp.stripe_coupon_id,
               sp.amount, sp.discount_amount, sp.currency
        FROM subscription_tiers st
        JOIN subscription_prices sp ON st.id = sp.subscription_tier_id
       WHERE st.id = $1 AND LOWER(sp.billing_type) = LOWER($2)
    """
    row = await DataBase.fetchrow(query, tier, billing_type)
    return row


async def insert_user_subscription(user_id: str, tier_id: int, billing_type: str, stripe_subscription_id: str):
    query = """
      INSERT INTO user_subscriptions
            (user_id, subscription_tier_id, stripe_subscription_id, status, start_date, next_billing_date)
      VALUES ($1, $2, $3, $4, $5, $6)
    """
    current_time = datetime.datetime.now()
    if billing_type.lower() == "monthly":
        next_billing_date = current_time + datetime.timedelta(days=30)
    elif billing_type.lower() == "annual":
        next_billing_date = current_time + datetime.timedelta(days=365)

    await DataBase.execute(query, user_id, tier_id, stripe_subscription_id, "active", current_time, next_billing_date)
    return True


async def insert_webhook_response(event_id: str, event_type: str, response: dict):
    query = """
      INSERT INTO stripe_webhook_events (event_id, event_type, event_data)
           VALUES ($1, $2, $3)
    """
    return await DataBase.execute(query, event_id, event_type, response)
