import json
from typing import List
from uuid import UUID

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


async def assign_permission_to_user(server_id: UUID, user_id: UUID, permission_id: List[UUID]):
    return await ServerRolePermission.assign_permission(server_id, user_id, permission_id)


async def remove_permission(server_id: UUID, user_id: UUID, permission_id: List[UUID]):
    return await ServerRolePermission.remove_permission(server_id, user_id, permission_id)
