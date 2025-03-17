-- up
CREATE TABLE user_notification_counters (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    server_id UUID NOT NULL,
    channel_id UUID NOT NULL,
    unread_count INT NOT NULL DEFAULT 0,
    mention_count INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_server_channel UNIQUE (user_id, server_id, channel_id)
);

CREATE INDEX idx_notification_counters_user ON user_notification_counters (user_id);

-- down
DROP TABLE IF EXISTS user_notification_counters;
