import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis
from starlette import status
from starlette.responses import JSONResponse

from app import constants
from app.api.v0.routers import limiter
from app.core.dependencies import get_current_user, get_redis
from app.models.channels import ChannelIn, ChannelOut, ChannelUpdate
from app.models.user import UserModel
from app.services.v0.audit_log_service import insert_audit_log
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
    redis: Redis = Depends(get_redis),
):
    """Create a new channel"""
    result = await create_channel(
        server_id=server_id, category_id=category_id, name=channel.name, description=channel.description, redis=redis
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category does not belong to the server")

    await insert_audit_log(
        user_id=current_user["username"],
        entity="channel",
        entity_id=server_id,
        action=constants.CREATE,
        changes=json.dumps({"action": f"Channel  {channel.name} created successfully by {current_user['username']}"}),
    )
    log.info(
        f"Channel created successfully: {channel.name} by Username:{current_user['username']}"
        f" & Id {current_user['id']}"
    )
    return {"message": "Channel created successfully", "channel": result}


@router.get("/{server_id}/{category_id}")
async def get_category_channels(server_id: str, category_id: str, redis: Redis = Depends(get_redis)):
    """Get all channels for a category"""
    result = await get_channels(server_id, category_id, redis)
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
    redis: Redis = Depends(get_redis),
):
    """Update a channel"""
    result = await update_channel(
        channel_id,
        server_id,
        name=channel.name,
        description=channel.description,
        position=channel.position,
        redis=redis,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid channel_id",
        )
    update_data = await request.json()
    existing_channel = await ChannelOut.get_channel(channel_id)
    changes = {
        key: {"before": getattr(existing_channel, key), "after": value}
        for key, value in update_data.items()
        if getattr(existing_channel, key) != value
    }
    if changes:
        await insert_audit_log(
            user_id=current_user["username"],
            entity="channel",
            entity_id=server_id,
            action=constants.UPDATE,
            changes=json.dumps(changes),
        )
    return {"message": "Channel updated successfully", "channel": result}


@router.delete("/{server_id}/{channel_id}")
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
async def delete_channel(
    server_id: str,
    channel_id: str,
    current_user: UserModel = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    """Delete a channel"""
    try:
        channel_name = await ChannelOut.get_channel(channel_id)
        await del_channel(server_id, channel_id, redis)

        await insert_audit_log(
            user_id=current_user["username"],
            entity="channel",
            entity_id=server_id,
            action=constants.DELETE,
            changes=json.dumps(
                {"action": f"Channel {channel_name.name} deleted successfully by {current_user['username']}"}
            ),
        )
        return {"message": "Channel deleted successfully"}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
