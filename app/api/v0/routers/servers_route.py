import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status

from app.core.dependencies import get_current_user
from app.models.server import ServerIn, ServerUpdate
from app.models.user import UserModel
from app.services.v0.permission_service import check_permissions
from app.services.v0.server_service import (
    create_server,
    get_all_user_servers,
    get_server_details_by_id,
    get_user_roles_permissions,
    join_server,
    leave_server,
    regenerate_invite_code,
    update_server,
)

router = APIRouter(dependencies=[Depends(get_current_user)])
log = logging.getLogger("fastapi")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_server(
    server: ServerIn,
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new server"""
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

    if not roles_permissions:
        raise HTTPException(status_code=404, detail="No roles or permissions found for the user in this server")
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


@router.post("/join/{invite_link}", status_code=status.HTTP_200_OK)
async def join_server_via_link(invite_link: str, current_user: UserModel = Depends(get_current_user)):
    """Join a server using an invitation link"""
    response = await join_server(invite_link, current_user)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code",
        )
    elif response and response[1] == "INSERT 0 0":
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="User has already joined the server")
    return {
        "message": "Successfully joined server:",
        "server_details": response[0].model_dump(),
    }


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
    response = await update_server(server_id, **update_data)
    updated_fields = {key: value for key, value in update_data.items() if value is not None}
    if response == "UPDATE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return {"message": "Successfully updated server", "server": updated_fields}


@router.patch("/regenerate_invite_code/{server_id}", status_code=status.HTTP_200_OK)
@check_permissions(["MANAGE_SERVER", "ADMINISTRATOR"])
async def re_generate_invite_code(server_id: str, current_user: UserModel = Depends(get_current_user)):
    """Create a new invite code for the server"""
    response = await regenerate_invite_code(server_id)
    return {"server_id": server_id, "invite_code": response}
