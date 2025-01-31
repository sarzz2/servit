-- up
ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;

-- down
ALTER TABLE users DROP COLUMN is_verified;
