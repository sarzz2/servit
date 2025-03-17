-- up

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_setting') THEN
        CREATE TYPE notification_setting AS ENUM ('all', 'mentions', 'none');
    END IF;
END$$;

-- Create the server_notification_settings table
CREATE TABLE IF NOT EXISTS server_notification_settings (
    user_id UUID NOT NULL,
    server_id UUID NOT NULL,
    notification_preference notification_setting NOT NULL DEFAULT 'all',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, server_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS server_config (
    server_id UUID PRIMARY KEY REFERENCES servers(id) ON DELETE CASCADE,
    default_notification_setting notification_setting NOT NULL DEFAULT 'all',
    max_members INTEGER NOT NULL DEFAULT 10000,
    max_categories INTEGER NOT NULL DEFAULT 50,
    max_channels INTEGER NOT NULL DEFAULT 150,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- down
DROP TABLE IF EXISTS server_notification_settings;
DROP TABLE IF EXISTS server_config;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_setting') THEN
        DROP TYPE notification_setting;
    END IF;
END$$;
