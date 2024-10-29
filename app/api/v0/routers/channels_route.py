import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status

from app.api.v0.routers import limiter
from app.core.dependencies import get_current_user
from app.models.channels import ChannelIn, ChannelUpdate
from app.models.user import UserModel
from app.services.v0.channels_service import (
    create_channel,
    del_channel,
    get_channels,
    update_channel,
)
from app.services.v0.permission_service import check_permissions

router = APIRouter(dependencies=[Depends(get_current_user)])
log = logging.getLogger("fastapi")


@router.post("/{server_id}/{category_id}", status_code=status.HTTP_201_CREATED)
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
@limiter.limit("25/minute")
async def create_new_channel(
    request: Request,
    server_id: str,
    category_id: str,
    channel: ChannelIn,
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new channel"""
    try:
        result = await create_channel(
            server_id=server_id,
            category_id=category_id,
            name=channel.name,
            description=channel.description,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Category does not belong to the server"
            )

    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category_id",
        )
    log.info(
        f"Channel created successfully: {channel.name} by Username:{current_user['username']}"
        f" & Id {current_user['id']}"
    )
    return {"message": "Channel created successfully", "channel": result}


@router.get("/{server_id}/{category_id}")
async def get_category_channels(server_id: str, category_id: str):
    """Get all channels for a category"""
    result = await get_channels(server_id, category_id)
    return result


@router.patch("/{server_id}/{channel_id}")
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
@limiter.limit("50/minute")
async def update_category_channel(
    request: Request,
    server_id: str,
    channel_id: str,
    channel: ChannelUpdate,
    current_user: UserModel = Depends(get_current_user),
):
    result = await update_channel(
        channel_id, name=channel.name, description=channel.description, position=channel.position
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid channel_id",
        )
    return {"message": "Channel updated successfully", "channel": result}


@router.delete("/{server_id}/{channel_id}")
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
async def delete_channel(server_id: str, channel_id: str, current_user: UserModel = Depends(get_current_user)):
    result = await del_channel(server_id, channel_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid channel_id",
        )
    return {"message": "Channel deleted successfully"}
