-- up
CREATE TABLE IF NOT EXISTS subscription_tiers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- e.g. "bronze", "silver", "diamond"
    description TEXT,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table to store pricing details for each tier
CREATE TABLE IF NOT EXISTS subscription_prices (
    id SERIAL PRIMARY KEY,
    subscription_tier_id INTEGER NOT NULL REFERENCES subscription_tiers(id),
    billing_type VARCHAR(10) NOT NULL, -- "monthly" or "annual"
    stripe_product_id VARCHAR(100),
    stripe_price_id VARCHAR(100),      -- Stripe price ID for the monthly subscription
    stripe_coupon_id VARCHAR(100),     -- For annual billing discount; coupon ID that applies discount for 12 months
    amount NUMERIC(10,2) NOT NULL,
    discount_amount NUMERIC(10,2),
    currency VARCHAR(10) DEFAULT 'inr',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (subscription_tier_id, billing_type)
);

-- Table for user subscriptions
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    subscription_tier_id INTEGER NOT NULL REFERENCES subscription_tiers(id),
    stripe_subscription_id VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    start_date TIMESTAMP,
    next_billing_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stripe_webhook_events (
    id SERIAL,
    event_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (created_at, id),
    UNIQUE (created_at, event_id)
);

SELECT create_hypertable(
    'stripe_webhook_events',
    'created_at',
    if_not_exists => TRUE
);

CREATE TYPE staff_roles AS ENUM ('superadmin', 'admin', 'staff', 'support');

CREATE TABLE IF NOT EXISTS staff(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    role staff_roles NOT NULL,
    password VARCHAR(100) NOT NULL,
    deleted_at TIMESTAMPTZ NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- down
DROP TABLE IF EXISTS user_subscriptions;
DROP TABLE IF EXISTS subscription_prices;
DROP TABLE IF EXISTS subscription_tiers;
DROP TABLE IF EXISTS stripe_webhook_events;
DROP type staff_roles;
DROP TABLE IF NOT EXISTS staff;
