import logging
from datetime import datetime
from typing import List, Optional

from asyncpg import Record

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


async def create_server(
    current_user, name: str, description: str, is_public: bool = False, server_picture_url: str = None
):
    return await ServerIn.create_server(name, description, current_user["id"], is_public, server_picture_url)


async def get_server_details_by_id(server_id: str):
    return await ServerOut.get_server_by_id(server_id)


async def get_all_user_servers(user_id):
    return await ServerOut.get_all_user_servers(user_id)


async def join_server(invite_link: str, current_user):
    server = await ServerOut.get_server_by_invite_code(invite_link)
    if server is None:
        raise ValueError("Invalid invite link")
    query = """
        SELECT * FROM server_bans
         WHERE server_id = $1 AND user_id = $2;
        """
    res = await DataBase.fetch(query, server.id, current_user["id"])
    if res:
        raise ValueError("You are banned from this server")
    return server, await ServerMembers.add_member(user_id=current_user["id"], server_id=server.id)


async def leave_server(server_id: str, current_user):
    return await ServerMembers.remove_member(user_id=current_user, server_id=server_id)


async def update_server(server_id: str, **kwargs):
    return await ServerUpdate.update_server(server_id, **kwargs)


async def get_user_roles_permissions(user_id, server_id):
    query = """
                WITH user_roles AS (
              SELECT r.id AS role_id, r.name AS role_name, r.description AS role_description, r.color AS role_color,
                     r.hierarchy AS hierarchy
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
              SELECT ur.role_id, ur.role_name, ur.role_description, ur.role_color, ur.hierarchy,
                     rp.permission_id, rp.permission_name
                FROM user_roles ur
           LEFT JOIN role_permissions rp ON rp.role_id = ur.role_id UNION ALL
              SELECT NULL AS role_id, NULL AS role_name, NULL AS role_description,
                     NULL AS role_color, NULL AS hierarchy,
                     p.id AS permission_id, p.name AS permission_name
                FROM server_permissions p
               WHERE p.name = 'OWNER' AND EXISTS (SELECT 1 FROM is_owner);
        """
    records = await DataBase.fetch(query, user_id, server_id)
    # Use sets to track unique roles and permissions
    unique_roles = {}
    unique_permissions = {}

    for record in records:
        # Add unique roles
        if record["role_id"] and record["role_name"]:
            unique_roles[record["role_name"]] = ServerRolesOut(
                id=record["role_id"],
                name=record["role_name"],
                description=record["role_description"],
                color=record["role_color"],
                hierarchy=record["hierarchy"],
                permissions="",
            )

        # Add unique permissions
        if record["permission_id"] and record["permission_name"]:
            unique_permissions[record["permission_id"]] = ServerPermission(
                id=record["permission_id"], name=record["permission_name"]
            )

    # Convert the unique dictionaries to lists
    roles = list(unique_roles.values())
    permissions = list(unique_permissions.values())

    if roles and permissions:
        return ServerRolesPermissionsResponse(serverId=server_id, roles=roles, permissions=permissions)
    return None


async def regenerate_invite_code(server_id: str):
    return await ServerUpdate.regenerate_invite_code(server_id)


async def get_all_server_users(server_id: str, limit: int, offset: int):
    query = """
        SELECT sm.user_id, sm.server_id, sm.nickname, sm.joined_at, sm.deleted_at, u.username
          FROM server_members sm
          JOIN users u ON sm.user_id = u.id
         WHERE sm.server_id = $1
      ORDER BY sm.joined_at DESC
         LIMIT $2 OFFSET $3;
    """
    return await DataBase.fetch(query, server_id, limit, offset)


async def kick_user(server_id: str, user_id: List[str]):
    query = """
        DELETE FROM server_members
              WHERE server_id = $1 AND user_id = ANY($2::uuid[]);
        """
    return await DataBase.execute(query, server_id, user_id)


async def ban_member_from_server(server_id: str, user_ids: List[str], reason: str):
    await kick_user(server_id, user_ids)
    query = """
        INSERT INTO server_bans (server_id, user_id, reason)
            SELECT $1, unnest($2::uuid[]), $3;

        """
    return await DataBase.execute(query, server_id, user_ids, reason)


async def unban_member_from_server(server_id: str, user_ids: List[str]):
    query = """
            DELETE FROM server_bans
                  WHERE server_id = $1 AND user_id = ANY($2::uuid[]);
            """
    result = await DataBase.execute(query, server_id, user_ids)
    if result == "DELETE 0":
        raise ValueError("User not banned")
    return result


async def get_audit_logs(
    server_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[DataBase] | list[Record]:
    query = """
       SELECT *
         FROM audit_logs
        WHERE entity_uuid = $1
          AND ($2::timestamptz IS NULL OR timestamp >= $2)
          AND ($3::timestamptz IS NULL OR timestamp <= $3)
          AND ($4::text IS NULL OR entity = $4)
     ORDER BY timestamp DESC
        LIMIT $5 OFFSET $6;
    """
    return await DataBase.fetch(query, server_id, start_time, end_time, event_type, limit, offset)
