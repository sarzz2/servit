-- up
-- Create table for category role assignments
CREATE TABLE category_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES server_roles(id) ON DELETE CASCADE,
    UNIQUE (category_id, role_id)
);

-- Create table for channel role assignments
CREATE TABLE channel_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES server_roles(id) ON DELETE CASCADE,
    UNIQUE (channel_id, role_id)
);

-- down
DROP TABLE IF EXISTS category_role_assignments;
DROP TABLE IF EXISTS channel_role_assignments;
