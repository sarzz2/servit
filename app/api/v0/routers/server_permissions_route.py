import json
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends
from redis import Redis
from starlette import status
from starlette.responses import JSONResponse

from app import constants
from app.core.dependencies import get_current_user, get_redis
from app.models.server_permissions import ServerPermission
from app.models.server_role_permissions import ServerRolePermission
from app.models.user import UserModel
from app.services.v0.audit_log_service import insert_audit_log
from app.services.v0.permission_service import check_permissions
from app.services.v0.server_permissions_service import (
    assign_permission_to_user,
    get_permissions,
    remove_permission,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
async def get_server_permissions(redis: Redis = Depends(get_redis)):
    """Get all server permissions"""
    permissions = await get_permissions(redis)
    return {"permissions": [permission for permission in permissions]}


@router.post("/{server_id}/{user_id}")
@check_permissions(["MANAGE_ROLES", "MANAGE_SERVER", "ADMINISTRATOR"])
async def assign_permissions_to_user(
    server_id: UUID, user_id: UUID, request: ServerRolePermission, current_user: UserModel = Depends(get_current_user)
):
    """Assign permissions to a specific user"""
    try:
        await assign_permission_to_user(server_id, user_id, request.permission_id)

        permissions = await ServerPermission.get_permissions(", ".join(map(str, request.permission_id)))
        user = await UserModel.get_users(str(user_id))
        permission_names = [permission.name for permission in permissions]
        await insert_audit_log(
            user_id=current_user["username"],
            entity="server permissions",
            entity_id=str(server_id),
            action=constants.CREATE,
            changes=json.dumps(
                {
                    "action": f"{current_user['username']} assigned {', '.join(permission_names)}"
                    f" permission to {user['username']}"
                }
            ),
        )
        return {"message": "Permission assigned successfully to user"}
    except asyncpg.exceptions.UniqueViolationError:
        return JSONResponse({"error": "Permission already assigned to user"}, status_code=status.HTTP_409_CONFLICT)
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        return JSONResponse({"error": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)


@router.delete("/{server_id}/{user_id}")
@check_permissions(["MANAGE_ROLES", "MANAGE_SERVER", "ADMINISTRATOR"])
async def remove_permissions_from_user(
    server_id: UUID, user_id: UUID, request: ServerRolePermission, current_user: UserModel = Depends(get_current_user)
):
    """Remove permission from a specific user"""
    try:
        await remove_permission(server_id, user_id, request.permission_id)

        permissions = await ServerPermission.get_permissions(", ".join(map(str, request.permission_id)))
        user = await UserModel.get_users(str(user_id))
        permission_names = [permission.name for permission in permissions]
        await insert_audit_log(
            user_id=current_user["username"],
            entity="server permissions",
            entity_id=str(server_id),
            action=constants.DELETE,
            changes=json.dumps(
                {
                    "action": f"{current_user['username']} removed {', '.join(permission_names)}"
                    f" permission from {user['username']}"
                }
            ),
        )
        return {"message": "Permission removed successfully from user"}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)


# TODO Create migrations for below functions first


async def assign_permission_to_category():
    pass


async def remove_permission_from_category():
    pass


async def assign_permission_to_channel():
    pass


async def remove_permission_from_channel():
    pass
