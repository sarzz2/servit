import json
from typing import List
from uuid import UUID

from app.core.database import DataBase
from app.models.server_permissions import ServerPermission
from app.models.server_role_permissions import ServerRolePermission


async def get_permissions(redis):
    cache_key = "permissions"
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    result = await ServerPermission.get_all_permissions()
    serializable_result = [perms.dict() for perms in result]
    await redis.set(cache_key, json.dumps(serializable_result, default=lambda o: str(o)))
    return result


async def assign_permission_to_user(server_id: UUID, user_id: UUID, permission_id: List[UUID]):
    return await ServerRolePermission.assign_permission(server_id, user_id, permission_id)


async def remove_permission(server_id: UUID, user_id: UUID, permission_id: List[UUID]):
    return await ServerRolePermission.remove_permission(server_id, user_id, permission_id)


async def assign_role_to_category(category_id: str, role_id: str):
    query = """
      INSERT INTO category_role_assignments (category_id, role_id)
      VALUES ($1, $2)
      ON CONFLICT (category_id, role_id) DO NOTHING
      RETURNING *;
      """
    res = await DataBase.fetchrow(query, category_id, role_id)
    if res is None:
        raise ValueError("Role Already assigned to category")
    return res


async def remove_role_from_category(category_id: str, role_id: str):
    query = """
    DELETE FROM category_role_assignments WHERE category_id = $1 AND role_id = $2"""
    res = await DataBase.execute(query, category_id, role_id)
    if res == "DELETE 0":
        raise ValueError("Role not assigned to category")
    return res
