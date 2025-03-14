import json
import logging
from datetime import datetime
from typing import List, Optional

import asyncpg
import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from starlette import status
from starlette.responses import JSONResponse

from app import constants
from app.api.v0.routers import limiter
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.server import ServerIn, ServerUpdate
from app.models.server_members import BanRequest
from app.models.user import UserModel
from app.services.v0.audit_log_service import insert_audit_log
from app.services.v0.permission_service import check_permissions
from app.services.v0.server_service import (
    ban_member_from_server,
    create_server,
    get_all_server_users,
    get_all_user_servers,
    get_audit_logs,
    get_banned_members_list,
    get_mutual_servers,
    get_server_details_by_id,
    get_user_roles_permissions,
    join_server,
    kick_user,
    leave_server,
    regenerate_invite_code,
    unban_member_from_server,
    update_server,
    user_server_count,
)

router = APIRouter(dependencies=[Depends(get_current_user)])
log = logging.getLogger("fastapi")


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def create_new_server(
    request: Request,
    server: ServerIn,
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new server"""
    result = await user_server_count(current_user)
    if result > 100:
        return JSONResponse({"error": "Reached maximum limit of 100 servers"}, status_code=status.HTTP_400_BAD_REQUEST)
    await create_server(current_user, **server.model_dump())

    log.info(
        f"Server created successfully: {server.name} by Username:{current_user['username']} & Id {current_user['id']}"
    )
    return {"message": "Server created successfully", "server": server.model_dump()}


@router.get("/user_servers", status_code=status.HTTP_200_OK)
async def get_user_servers(current_user: UserModel = Depends(get_current_user)):
    """Get all servers joined by the user"""
    servers = await get_all_user_servers(current_user["id"])
    return {"servers": [server.model_dump() for server in servers]}


@router.get("/{server_id}/roles_permissions")
async def get_server_roles_permissions(server_id: str, current_user: UserModel = Depends(get_current_user)):
    roles_permissions = await get_user_roles_permissions(current_user["id"], server_id)
    return roles_permissions


@router.get("/{server_id}", status_code=status.HTTP_200_OK)
async def get_server_by_id(server_id: str):
    """Get server details by ID"""
    # Fetch server details by ID
    server = await get_server_details_by_id(server_id)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    return {"server": server.model_dump()}


@router.get("/mutual_servers/{user_id}", status_code=status.HTTP_200_OK)
async def mutual_server(user_id: str, current_user: UserModel = Depends(get_current_user)):
    """Get Mutual servers with the user id passed"""
    try:
        return await get_mutual_servers(user_id, current_user["id"])
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)


@router.get("/audit_logs/{server_id}")
@check_permissions(["MANAGE_SERVER", "ADMINISTRATOR"])
async def get_server_audit_logs(
    server_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time for filtering logs"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering logs"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    action: Optional[str] = Query(None, description="Filter by action performed"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        # Calculate the offset for pagination
        offset = (page - 1) * per_page
        logs = await get_audit_logs(server_id, start_time, end_time, event_type, action, limit=per_page, offset=offset)

        return {"page": page, "per_page": per_page, "count": len(logs), "logs": logs}
    except Exception as e:
        log.error(e)
        return JSONResponse(
            {"error": "Failed to retrieve audit logs"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/join/{invite_link}", status_code=status.HTTP_200_OK)
async def join_server_via_link(invite_link: str, current_user: UserModel = Depends(get_current_user)):
    """Join a server using an invitation link"""
    try:
        result = await user_server_count(current_user)
        if result > 100:
            return JSONResponse(
                {"error": "Reached maximum limit of 100 servers"}, status_code=status.HTTP_400_BAD_REQUEST
            )
        response = await join_server(invite_link, current_user)
        if response and response[1] == "INSERT 0 0":
            raise HTTPException(status_code=status.HTTP_302_FOUND, detail="User has already joined the server")
        return {
            "message": "Successfully joined server:",
            "server_details": response[0].model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/leave/{server_id}", status_code=status.HTTP_200_OK)
async def leave_from_server(server_id: str, current_user: UserModel = Depends(get_current_user)):
    """Leave a server"""
    await leave_server(server_id, current_user["id"])
    return {"message": "Successfully left server"}


@router.patch("/{server_id}", status_code=status.HTTP_200_OK)
@check_permissions(["MANAGE_SERVER", "ADMINISTRATOR"])
async def update_server_by_id(
    server_id: str, request: Request, server: ServerUpdate, current_user: UserModel = Depends(get_current_user)
):
    """Update server details"""
    update_data = await request.json()
    existing_server = (await get_server_details_by_id(server_id)).model_dump()
    changes = {
        key: {"before": existing_server[key], "after": value}
        for key, value in update_data.items()
        if existing_server.get(key) != value
    }

    await update_server(server_id, **update_data)
    updated_fields = {key: value for key, value in update_data.items() if value is not None}
    if changes:
        await insert_audit_log(
            user_id=current_user["username"],
            entity="server",
            entity_id=server_id,
            action=constants.UPDATE,
            changes=json.dumps(changes),
        )
    return {"message": "Successfully updated server", "server": updated_fields}


@router.patch("/regenerate_invite_code/{server_id}", status_code=status.HTTP_200_OK)
@check_permissions(["MANAGE_SERVER", "ADMINISTRATOR"])
@limiter.limit("5/minute")
async def re_generate_invite_code(
    request: Request, server_id: str, current_user: UserModel = Depends(get_current_user)
):
    """Create a new invite code for the server"""
    existing_server = (await get_server_details_by_id(server_id)).model_dump()
    old_invite_code = existing_server["invite_code"]

    response = await regenerate_invite_code(server_id)
    await insert_audit_log(
        user_id=current_user["username"],
        entity="server",
        entity_id=server_id,
        action=constants.UPDATE,
        changes=json.dumps({"invite_code": {"before": old_invite_code, "after": response}}),
    )
    return {"server_id": server_id, "invite_code": response}


@router.get("/all_users/{server_id}", status_code=status.HTTP_200_OK)
async def get_server_users(
    request: Request,
    server_id: str,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get paginated list of all users in a server with their online statuses"""
    users = await get_all_server_users(server_id, limit, offset)

    online_users = {}
    try:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split(" ")[1]
        if token:
            response = requests.get(f"{settings.GO_BASE_URL}/friends/online?token={token}")
            response.raise_for_status()
            online_users = {user["userId"]: user["status"] for user in response.json()}
    except requests.exceptions.RequestException as e:
        log.error(f"Failed to fetch online users: {e}")

    # Merge online status into user data
    users = [dict(user) for user in users]

    for user in users:
        user["status"] = online_users.get(str(user["user_id"]), "offline")

    return {"users": users, "limit": limit, "offset": offset}


@router.post("/kick_user/{server_id}", status_code=status.HTTP_200_OK)
@check_permissions(["MANAGE_SERVER", "ADMINISTRATOR", "KICK_MEMBERS", "BAN_MEMBERS"])
async def kick_server_user(
    request: Request, server_id: str, user_ids: List[str], current_user: UserModel = Depends(get_current_user)
):
    """Kick a list of users from the server"""
    response = await kick_user(server_id, user_ids)
    if response == "DELETE 0":
        return JSONResponse({"message": "User does not exist"}, status_code=status.HTTP_400_BAD_REQUEST)

    user_ids_string = ", ".join(map(str, user_ids))
    users = await UserModel.get_users(user_ids_string)
    await insert_audit_log(
        user_id=current_user["username"],
        entity="server",
        entity_id=server_id,
        action=constants.KICK_USER,
        changes=json.dumps({"action": f"{current_user['username']} kicked {users}"}),
    )
    return {"message": "user kicked from server successfully"}


@router.post("/ban/{server_id}", status_code=status.HTTP_200_OK)
@check_permissions(["MANAGE_SERVER", "ADMINISTRATOR", "KICK_MEMBERS", "BAN_MEMBERS"])
async def ban_member(
    server_id: str,
    ban_request: BanRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Ban one or more members from the server.
    """
    try:
        await ban_member_from_server(server_id, ban_request.user_ids, ban_request.reason)

        users = await UserModel.get_users(", ".join(map(str, ban_request.user_ids)))
        await insert_audit_log(
            user_id=current_user["username"],
            entity="server",
            entity_id=server_id,
            action=constants.BAN_USER,
            changes=json.dumps({"action": f"{current_user['username']} banned {users}"}),
        )
        return {"message": "Member banned successfully"}
    except asyncpg.UniqueViolationError:
        return JSONResponse(
            {"error": "User is already banned from the server"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return {"error": str(e)}


@router.post("/unban/{server_id}", status_code=status.HTTP_200_OK)
@check_permissions(["MANAGE_SERVER", "ADMINISTRATOR", "KICK_MEMBERS", "BAN_MEMBERS"])
async def unban_member(
    server_id: str,
    ban_request: BanRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Unban a member from the server.
    """
    try:
        await unban_member_from_server(server_id, ban_request.user_ids)
        users = await UserModel.get_users(", ".join(map(str, ban_request.user_ids)))
        await insert_audit_log(
            user_id=current_user["username"],
            entity="server",
            entity_id=server_id,
            action=constants.UNBAN_USER,
            changes=json.dumps({"action": f"{current_user['username']} unbanned {users}"}),
        )
        return {"message": "Member unbanned successfully"}
    except ValueError as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("/banned/{server_id}")
@check_permissions(["MANAGE_SERVER", "ADMINISTRATOR", "KICK_MEMBERS", "BAN_MEMBERS"])
async def banned_members(
    request: Request,
    server_id: str,
    limit: int = Query(25, ge=1, le=100),
    per_page: int = Query(25, ge=0, le=100),
    search_query: str = Query(None, description="Search Keyword"),
    current_user: UserModel = Depends(get_current_user),
):
    """Get list of banned members in a server"""
    return await get_banned_members_list(server_id, search_query, limit, per_page)
