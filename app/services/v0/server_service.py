import logging
from typing import List

from app.core.database import DataBase
from app.models.server import ServerIn, ServerOut, ServerUpdate
from app.models.server_members import ServerMembers
from app.models.server_permissions import ServerPermission
from app.models.server_roles import ServerRolesOut

log = logging.getLogger("fastapi")


class ServerRolesPermissionsResponse(DataBase):
    serverId: str
    roles: List[ServerRolesOut]
    permissions: List[ServerPermission]


async def create_server(current_user, name: str, description: str, is_public: bool = False):
    return await ServerIn.create_server(name, description, current_user["id"], is_public)


async def get_server_details_by_id(server_id: str):
    return await ServerOut.get_server_by_id(server_id)


async def get_all_user_servers(user_id):
    return await ServerOut.get_all_user_servers(user_id)


async def join_server(invite_link: str, current_user):
    server = await ServerOut.get_server_by_invite_code(invite_link)
    if server is None:
        return None
    await ServerMembers.add_member(user_id=current_user["id"], server_id=server.id)
    return server


async def leave_server(server_id: str, current_user):
    return await ServerMembers.remove_member(user_id=current_user, server_id=server_id)


async def update_server(server_id: str, **kwargs):
    return await ServerUpdate.update_server(server_id, **kwargs)


async def get_user_roles_permissions(user_id, server_id):
    query = """
                WITH user_roles AS (
    SELECT r.id AS role_id, r.name AS role_name
    FROM server_user_roles sur
    JOIN server_roles r ON r.id = sur.role_id
    WHERE sur.user_id = $1 AND r.server_id = $2
),
role_permissions AS (
    SELECT rp.role_id, p.id AS permission_id, p.name AS permission_name
    FROM server_role_permissions rp
    JOIN server_permissions p ON p.id = rp.permission_id
    WHERE rp.role_id IN (SELECT role_id FROM user_roles)
),
is_owner AS (
    SELECT owner_id from servers s
    WHERE s.owner_id = $1 AND s.id = $2
    LIMIT 1
)
SELECT ur.role_id, ur.role_name, rp.permission_id, rp.permission_name
FROM user_roles ur
LEFT JOIN role_permissions rp ON rp.role_id = ur.role_id
UNION ALL
SELECT NULL AS role_id, NULL AS role_name, p.id AS permission_id, p.name AS permission_name
FROM server_permissions p
WHERE p.name = 'OWNER'
AND EXISTS (SELECT 1 FROM is_owner);
        """
    records = await DataBase.fetch(query, user_id, server_id)
    # Use sets to track unique roles and permissions
    unique_roles = {}
    unique_permissions = {}

    for record in records:
        # Add unique roles
        if record["role_id"] and record["role_name"]:
            unique_roles[record["role_name"]] = ServerRolesOut(id=record["role_id"], name=record["role_name"])

        # Add unique permissions
        if record["permission_id"] and record["permission_name"]:
            unique_permissions[record["permission_id"]] = ServerPermission(
                id=record["permission_id"], name=record["permission_name"]
            )

    # Convert the unique dictionaries to lists
    roles = list(unique_roles.values())
    permissions = list(unique_permissions.values())

    return ServerRolesPermissionsResponse(serverId=server_id, roles=roles, permissions=permissions)
