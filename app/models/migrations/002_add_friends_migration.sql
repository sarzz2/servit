-- up
CREATE TYPE friend_status AS ENUM ('pending', 'accepted', 'rejected', 'blocked');

CREATE TABLE friends (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    friend_id UUID NOT NULL,
    status friend_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, friend_id), -- Ensure one friendship per pair
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id) ON DELETE CASCADE, -- Delete friendship if user is deleted
    CONSTRAINT fk_friend
        FOREIGN KEY(friend_id)
        REFERENCES users(id) ON DELETE CASCADE -- Delete friendship if friend is deleted
);

-- Function to update the timestamp of a row
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Trigger to update the updated_at timestamp on row updates
CREATE TRIGGER update_friends_updated_at
BEFORE UPDATE ON friends
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- down
DROP TABLE IF EXISTS friends CASCADE;
DROP TYPE IF EXISTS friend_status;
DROP FUNCTION IF EXISTS update_timestamp;

