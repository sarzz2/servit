import logging

import asyncpg
from fastapi import APIRouter, Depends
from redis import Redis
from starlette import status

from app.core.dependencies import get_current_user, get_redis
from app.models.server_notifications import BatchNotificationCounterUpdate
from app.models.user import UserModel
from app.services.v0.server_notifications_service import (
    clear_channel_notification,
    get_batch_notification,
    get_notification_preference,
    insert_batch_notifications,
    update_notification_preference,
)

router = APIRouter(dependencies=[Depends(get_current_user)])
log = logging.getLogger("fastapi")


@router.get("/{server_id}", status_code=status.HTTP_200_OK)
async def get_notification(
    server_id: str,
    redis: Redis = Depends(get_redis),
    current_user: UserModel = Depends(get_current_user),
):
    """Get Notification Preference for the current user on a specific server"""

    res = await get_notification_preference(redis, current_user["id"], server_id)
    return {"notification_preference": res}


@router.post("/{server_id}/{notification_preference}", status_code=status.HTTP_200_OK)
async def notification(
    server_id: str,
    notification_preference: str,
    redis: Redis = Depends(get_redis),
    current_user: UserModel = Depends(get_current_user),
):
    """Update Notification Preference of the user"""
    try:
        await update_notification_preference(redis, current_user["id"], server_id, notification_preference)
        return {"message": "Notification Preference Updated"}
    except asyncpg.InvalidTextRepresentationError:
        return {"error": "Invalid Notification Preference"}


@router.get("/counters/{user_id}")
async def batch_notifications(user_id: str):
    return await get_batch_notification(user_id)


@router.post("/counters")
async def update_batch_notifications(
    update_data: BatchNotificationCounterUpdate,
):
    """Batch update notification counters."""
    if not update_data.updates:
        return {"message": "No updates"}

    await insert_batch_notifications(update_data.updates)


@router.delete("/clear/{server_id}/{channel_id}/{user_id}")
async def clear_notifications(server_id: str, channel_id: str, user_id: str):
    return await clear_channel_notification(server_id, channel_id, user_id)
