-- up
CREATE TABLE IF NOT EXISTS additional_user_details (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE,
    gender VARCHAR(20),
    phone VARCHAR(20),
    address TEXT,
    country TEXT,
    bio TEXT,
    profile_banner_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- down
DROP TABLE IF EXISTS additional_user_details;
