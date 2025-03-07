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


async def user_server_count(current_user):
    query = """
    SELECT DISTINCT COUNT(*) FROM server_members WHERE user_id = $1"""
    return await DataBase.fetchval(query, current_user["id"])


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


async def get_mutual_servers(user_id: str, current_user_id: str):
    query = """
            SELECT s.* FROM servers AS s
             WHERE s.id IN (SELECT a.server_id
            FROM server_members AS a
            JOIN server_members AS b
              ON a.server_id = b.server_id
            WHERE a.user_id = $2
              AND b.user_id = $1);
            """
    return await DataBase.fetch(query, current_user_id, user_id)


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
        SELECT sm.user_id, sm.server_id, sm.nickname, sm.joined_at, sm.deleted_at,
                u.username, u.profile_picture_url,
      COALESCE(
              json_agg(DISTINCT jsonb_build_object('id', r.id, 'name', r.name))
              FILTER (WHERE r.id IS NOT NULL), null
            )
            AS roles,
      COALESCE(
              json_agg(DISTINCT jsonb_build_object('id', sp.id, 'name', sp.name))
              FILTER (WHERE sp.id IS NOT NULL),
              null
          ) AS permissions
          FROM server_members sm
          JOIN users u ON sm.user_id = u.id
     LEFT JOIN server_user_roles sr ON sm.user_id = sr.user_id
     LEFT JOIN server_roles r ON sr.role_id = r.id
           AND r.server_id = $1
     LEFT JOIN server_user_permissions sup ON sm.user_id = sup.user_id
     LEFT JOIN server_permissions sp ON sup.permission_id = sp.id
           AND sm.server_id = $1
         WHERE sm.server_id = $1
      GROUP BY sm.user_id, sm.server_id, sm.nickname, sm.joined_at, sm.deleted_at, u.username, u.profile_picture_url
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


async def get_banned_members_list(server_id: str, search_query: str, page: int, per_page: int):
    query = """
    SELECT sb.reason, sb.created_at, sb.user_id,
             u.username, u.profile_picture_url
      FROM server_bans sb
      JOIN users u ON sb.user_id = u.id
     WHERE server_id = $1
           AND (
               $2::text IS NULL
               OR $2::text = ''
               OR u.username ILIKE '%' || $2::text || '%'
          )
     LIMIT $3 OFFSET $4"""
    offset = (page - 1) * per_page
    return await DataBase.fetch(query, search_query, server_id, page, offset)


async def get_audit_logs(
    server_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_type: Optional[str] = None,
    action: Optional[str] = None,
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
          AND ($5::text is NULL or action = $5)
     ORDER BY timestamp DESC
        LIMIT $6 OFFSET $7;
    """
    return await DataBase.fetch(query, server_id, start_time, end_time, event_type, action, limit, offset)
