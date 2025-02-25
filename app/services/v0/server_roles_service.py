from typing import List
from uuid import UUID

from fastapi.exceptions import HTTPException
from starlette import status

from app.models.server_roles import ServerRolesIn, ServerRolesOut, ServerRoleUpdate
from app.models.server_user_roles import ServerUserRolesIn


async def create_role(server_id: UUID, name: str, description: str, color: str, permissions: List[str]):
    try:
        await ServerRolesIn.new_role_with_permissions(server_id, name, description, color, permissions)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def get_role(server_id: UUID, page: int = 1, per_page: int = 25):
    return await ServerRolesOut.get_role(server_id, page, per_page)


async def update_role(role_id: UUID, update_data):
    return await ServerRoleUpdate.update_server_role(role_id, update_data)


async def delete_role(role_id: UUID):
    if await ServerRolesIn.delete_role(role_id):
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role with given id does not exist.")


async def assign_role(role_id: UUID, server_id: UUID, user_id: UUID):
    return await ServerUserRolesIn.assign_role_to_user(user_id, role_id, server_id)


async def remove_role(role_id: UUID, server_id: UUID, user_id: UUID):
    return await ServerUserRolesIn.remove_role_from_user(user_id, role_id, server_id)
