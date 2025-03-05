-- up
-- Indexes for Users Table
CREATE INDEX idx_users_deleted_at ON users(deleted_at);

-- Indexes for Servers Table
CREATE INDEX idx_servers_owner_id ON servers(owner_id);
CREATE INDEX idx_servers_is_public ON servers(is_public);
CREATE INDEX idx_servers_name ON servers(name);

-- Indexes for Server_Members Table
CREATE INDEX idx_server_members_user_id ON server_members(user_id);
CREATE INDEX idx_server_members_server_id ON server_members(server_id);
CREATE INDEX idx_server_members_deleted_at ON server_members(deleted_at);

-- Indexes for Server_Roles Table
CREATE INDEX idx_server_roles_server_id ON server_roles(server_id);
CREATE INDEX idx_server_roles_hierarchy_2 ON server_roles(hierarchy);

-- Indexes for Server_Role_Permissions Table
-- Primary key covers (role_id, permission_id), but for queries filtering by permission_id:
CREATE INDEX idx_server_role_permissions_permission_id ON server_role_permissions(permission_id);

-- Indexes for Server_User_Roles Table
CREATE INDEX idx_server_user_roles_role_id ON server_user_roles(role_id);

-- Indexes for Server_Denied_Permissions Table
CREATE INDEX idx_server_denied_permissions_permission_id ON server_denied_permissions(permission_id);

-- Indexes for Server_User_Permissions Table
CREATE INDEX idx_server_user_permissions_permission_id ON server_user_permissions(permission_id);

-- Indexes for Categories Table
CREATE INDEX idx_categories_server_id ON categories(server_id);

-- Indexes for Channels Table
CREATE INDEX idx_channels_server_id ON channels(server_id);
CREATE INDEX idx_channels_category_id ON channels(category_id);
CREATE INDEX idx_channels_type ON channels(type);

-- Indexes for Friends Table
CREATE INDEX idx_friends_user_id ON friends(user_id);
CREATE INDEX idx_friends_friend_id ON friends(friend_id);
CREATE INDEX idx_friends_status ON friends(status);

-- Indexes for Server_Bans Table
CREATE INDEX idx_server_bans_server_id ON server_bans(server_id);
CREATE INDEX idx_server_bans_user_id ON server_bans(user_id);

-- Indexes for Subscription_Tiers Table
CREATE INDEX idx_subscription_tiers_deleted_at ON subscription_tiers(deleted_at);

-- Indexes for Subscription_Prices Table
CREATE INDEX idx_subscription_prices_subscription_tier_id ON subscription_prices(subscription_tier_id);

-- Indexes for User_Subscriptions Table
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_subscription_tier_id ON user_subscriptions(subscription_tier_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);

-- Indexes for Staff Table
CREATE INDEX idx_staff_phone ON staff(phone);
CREATE INDEX idx_staff_role ON staff(role);
CREATE INDEX idx_staff_deleted_at ON staff(deleted_at);

-- down

DROP INDEX IF EXISTS idx_users_deleted_at;
DROP INDEX IF EXISTS idx_servers_owner_id;
DROP INDEX IF EXISTS idx_servers_is_public;
DROP INDEX IF EXISTS idx_servers_name;
DROP INDEX IF EXISTS idx_server_members_user_id;
DROP INDEX IF EXISTS idx_server_members_server_id;
DROP INDEX IF EXISTS idx_server_members_deleted_at;
DROP INDEX IF EXISTS idx_server_roles_server_id;
DROP INDEX IF EXISTS idx_server_roles_hierarchy_2;
DROP INDEX IF EXISTS idx_server_role_permissions_permission_id;
DROP INDEX IF EXISTS idx_server_user_roles_role_id;
DROP INDEX IF EXISTS idx_server_denied_permissions_permission_id;
DROP INDEX IF EXISTS idx_server_user_permissions_permission_id;
DROP INDEX IF EXISTS idx_categories_server_id;
DROP INDEX IF EXISTS idx_channels_server_id;
DROP INDEX IF EXISTS idx_channels_category_id;
DROP INDEX IF EXISTS idx_channels_type;
DROP INDEX IF EXISTS idx_friends_user_id;
DROP INDEX IF EXISTS idx_friends_friend_id;
DROP INDEX IF EXISTS idx_friends_status;
DROP INDEX IF EXISTS idx_server_bans_server_id;
DROP INDEX IF EXISTS idx_server_bans_user_id;
DROP INDEX IF EXISTS idx_subscription_tiers_deleted_at;
DROP INDEX IF EXISTS idx_subscription_prices_subscription_tier_id;
DROP INDEX IF EXISTS idx_user_subscriptions_user_id;
DROP INDEX IF EXISTS idx_user_subscriptions_subscription_tier_id;
DROP INDEX IF EXISTS idx_user_subscriptions_status;
DROP INDEX IF EXISTS idx_stripe_webhook_events_event_type;
DROP INDEX IF EXISTS idx_staff_phone;
DROP INDEX IF EXISTS idx_staff_role;
DROP INDEX IF EXISTS idx_staff_deleted_at;
