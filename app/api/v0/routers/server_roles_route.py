import json
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from starlette.responses import JSONResponse

from app import constants
from app.core.dependencies import get_current_user
from app.models.server_roles import ServerRolesIn, ServerRolesOut, ServerRoleUpdate
from app.models.user import UserModel
from app.services.v0.audit_log_service import insert_audit_log
from app.services.v0.permission_service import check_permissions
from app.services.v0.server_roles_service import (
    assign_role,
    create_role,
    delete_role,
    get_role,
    remove_role,
    update_role,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/{server_id}", status_code=201)
@check_permissions(["MANAGE_ROLES", "MANAGE_SERVER", "ADMINISTRATOR"])
async def create_server_role(
    server_id: UUID, server_role: ServerRolesIn, current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new server role with permissions.
    """
    if not server_role.permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one permission is required",
        )
    try:
        await create_role(
            server_id,
            server_role.name,
            server_role.description,
            server_role.color,
            server_role.permissions,
        )
        await insert_audit_log(
            user_id=current_user["id"],
            entity="roles",
            entity_id=str(server_id),
            action=constants.CREATE,
            changes=json.dumps(
                {"action": f"Role {server_role.name} created successfully by {current_user['username']}"}
            ),
        )
        return {"message": "Role created successfully", "Role": server_role.model_dump()}
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Role with {server_role.name} already exists."
        )


@router.get("/{server_id}", status_code=200)
@check_permissions(["MANAGE_ROLES", "MANAGE_SERVER", "ADMINISTRATOR"])
async def get_server_role(server_id: UUID, current_user: UserModel = Depends(get_current_user)):
    """
    Fetch the details of a specific server role, including its permissions.
    """
    return await get_role(server_id=server_id)


@router.patch("/{server_id}/{role_id}", status_code=200)
@check_permissions(["MANAGE_ROLES", "MANAGE_SERVER", "ADMINISTRATOR"])
async def update_server_role(
    request: Request,
    role_id: UUID,
    server_id: UUID,
    update_data: ServerRoleUpdate,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update the server role's details and its permissions.
    """
    try:
        existing_role = await ServerRolesOut.get_role_by_id(role_id)
        await update_role(role_id, update_data)
        updated_data = await request.json()
        changes = {
            key: {"before": getattr(existing_role, key), "after": value}
            for key, value in updated_data.items()
            if getattr(existing_role, key) != value
        }
        if changes:
            await insert_audit_log(
                user_id=current_user["id"],
                entity="roles",
                entity_id=str(server_id),
                action=constants.UPDATE,
                changes=json.dumps(changes),
            )
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Role with {update_data.name} already exists."
        )

    return update_data.model_dump()


@router.delete("/{server_id}/{role_id}", status_code=200)
@check_permissions(["MANAGE_ROLES", "MANAGE_SERVER", "ADMINISTRATOR"])
async def delete_server_role(role_id: UUID, server_id: UUID, current_user: UserModel = Depends(get_current_user)):
    """
    Delete a server role and clean up related data.
    """
    existing_role = await ServerRolesOut.get_role_by_id(role_id)
    await delete_role(role_id)
    await insert_audit_log(
        user_id=current_user["id"],
        entity="roles",
        entity_id=str(server_id),
        action=constants.DELETE,
        changes=json.dumps({"action": f"Role {existing_role.name} deleted successfully by {current_user['username']}"}),
    )
    return {"message": "Role deleted successfully"}


@router.post("/{server_id}/{role_id}/{user_id}")
@check_permissions(["MANAGE_ROLES", "MANAGE_SERVER", "ADMINISTRATOR"])
async def assign_role_to_user(
    role_id: UUID, server_id: UUID, user_id: UUID, current_user: UserModel = Depends(get_current_user)
):
    """Assign a role to the user"""
    try:
        if await assign_role(role_id, server_id, user_id):
            role = await ServerRolesOut.get_role_by_id(role_id)
            user = await UserModel.get_users(str(user_id))
            await insert_audit_log(
                user_id=current_user["id"],
                entity="roles",
                entity_id=str(server_id),
                action=constants.UPDATE,
                changes=json.dumps(
                    {
                        "action": f"Role {role.name} successfully assigned to {user['username']}"
                        f" by {current_user['username']}"
                    }
                ),
            )
            return {"message": "Role assigned successfully to user"}
        return JSONResponse({"error": "User does not exist in server"}, status_code=status.HTTP_400_BAD_REQUEST)
    except asyncpg.exceptions.UniqueViolationError:
        return JSONResponse({"error": "User already has the role"}, status_code=status.HTTP_409_CONFLICT)


@router.delete("/{server_id}/{role_id}/{user_id}")
@check_permissions(["MANAGE_ROLES", "MANAGE_SERVER", "ADMINISTRATOR"])
async def remove_role_from_user(
    role_id: UUID, server_id: UUID, user_id: UUID, current_user: UserModel = Depends(get_current_user)
):
    """Remove a role to the user"""
    if await remove_role(role_id, server_id, user_id):
        role = await ServerRolesOut.get_role_by_id(role_id)
        user = await UserModel.get_users(str(user_id))
        await insert_audit_log(
            user_id=current_user["id"],
            entity="roles",
            entity_id=str(server_id),
            action=constants.UPDATE,
            changes=json.dumps(
                {
                    "action": f"Role {role.name} successfully removed from {user['username']}"
                    f" by {current_user['username']}"
                }
            ),
        )
        return {"message": "Role removed successfully from user"}
    return JSONResponse({"error": "User does not exist in server"}, status_code=status.HTTP_400_BAD_REQUEST)
