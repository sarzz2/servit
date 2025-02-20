from typing import List
from uuid import UUID

from app.models.server_role_permissions import ServerRolePermission


async def assign_permission_to_user(server_id: UUID, user_id: UUID, permission_id: List[UUID]):
    return await ServerRolePermission.assign_permission(server_id, user_id, permission_id)


async def remove_permission(server_id: UUID, user_id: UUID, permission_id: List[UUID]):
    return await ServerRolePermission.remove_permission(server_id, user_id, permission_id)
