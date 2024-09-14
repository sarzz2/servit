-- up
-- Create Users Table

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create Servers Table
CREATE TABLE IF NOT EXISTS servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL,
    invite_code VARCHAR(20) UNIQUE NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    max_members INTEGER DEFAULT 10000,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create Server_Members Table to link users and servers
CREATE TABLE IF NOT EXISTS server_members (
    user_id UUID NOT NULL,
    server_id UUID NOT NULL,
    nickname VARCHAR(255),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, server_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

-- Create Server_Roles Table
CREATE TABLE IF NOT EXISTS server_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    hierarchy INTEGER DEFAULT 0,
    color VARCHAR(7) DEFAULT '#000000',
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    UNIQUE (server_id, name)
);

-- Create Server_Permissions Table
CREATE TABLE IF NOT EXISTS server_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    UNIQUE (server_id, name)
);

-- Create Server_Role_Permissions Table to link roles and permissions within a server
CREATE TABLE IF NOT EXISTS server_role_permissions (
    role_id UUID NOT NULL,
    permission_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES server_roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES server_permissions(id) ON DELETE CASCADE
);

-- Create Server_User_Roles Table to link users and roles within a server
CREATE TABLE IF NOT EXISTS server_user_roles (
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES server_roles(id) ON DELETE CASCADE
);

-- Create Server_Denied_Permissions Table to handle denied permissions within a server
CREATE TABLE IF NOT EXISTS server_denied_permissions (
    role_id UUID NOT NULL,
    permission_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES server_roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES server_permissions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS server_user_permissions (
    user_id UUID NOT NULL,
    permission_id UUID NOT NULL,
    granted BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, permission_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES server_permissions(id) ON DELETE CASCADE
);

-- Create Categories Table
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    server_id UUID REFERENCES servers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    position INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_position_per_server UNIQUE (server_id, position)
);

-- Create Channels Table
CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

-- down
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS channels;
DROP TABLE IF EXISTS server_user_permissions;
DROP TABLE IF EXISTS server_denied_permissions;
DROP TABLE IF EXISTS server_user_roles;
DROP TABLE IF EXISTS server_role_permissions;
DROP TABLE IF EXISTS server_permissions;
DROP TABLE IF EXISTS server_roles;
DROP TABLE IF EXISTS server_members;
DROP TABLE IF EXISTS servers;
DROP TABLE IF EXISTS users;
