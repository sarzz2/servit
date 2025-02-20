from typing import List
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v0.routers import limiter
from app.core.dependencies import get_current_user
from app.models.friend_requests import FriendRequest
from app.models.user import UserModel
from app.services.v0.friend_requests_service import FriendService

router = APIRouter()


@router.post("/{friend_id}", status_code=status.HTTP_201_CREATED)
@limiter.limit("500/hour")
async def send_friend_request(request: Request, friend_id: UUID, current_user: UserModel = Depends(get_current_user)):
    """Send a new friend request to another user"""
    if friend_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot send a friend request to yourself")
    try:
        await FriendService.send_friend_request(current_user["id"], friend_id)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="Friend request already sent")
    return {"message": "Friend request sent successfully"}


@router.patch("/{friend_id}/{status}", status_code=status.HTTP_200_OK)
async def update_friend_status(friend_id: UUID, status: str, current_user: UserModel = Depends(get_current_user)):
    """Update sent friend request (Accept, Reject etc.)"""
    valid_statuses = ["pending", "accepted", "rejected", "blocked"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    result = await FriendService.update_friend_status(current_user["id"], friend_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Friend request not found")
    return result


@router.delete("/cancel/{friend_id}", status_code=status.HTTP_200_OK)
async def cancel_friend_request(friend_id: UUID, current_user: UserModel = Depends(get_current_user)):
    """Cancel outgoing friend request"""
    result = await FriendService.cancel_request(current_user["id"], friend_id)
    if not result:
        raise HTTPException(status_code=404, detail="Friend request not found")
    return result


@router.get("/", response_model=List[FriendRequest], status_code=status.HTTP_200_OK)
async def get_friends(current_user: UserModel = Depends(get_current_user)):
    friends = await FriendService.get_all_friends(current_user["id"])
    return friends


@router.get("/requests", response_model=List[FriendRequest], status_code=status.HTTP_200_OK)
async def get_friend_requests(current_user: UserModel = Depends(get_current_user)):
    requests = await FriendService.get_pending_requests(current_user["id"])
    return requests


@router.get("/blocked", response_model=List[FriendRequest], status_code=status.HTTP_200_OK)
async def get_blocked_friends(current_user: UserModel = Depends(get_current_user)):
    blocked = await FriendService.get_blocked_friends(current_user["id"])
    return blocked


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(friend_id: UUID, current_user: UserModel = Depends(get_current_user)):
    result = await FriendService.remove_friend(current_user["id"], friend_id)
    if not result:
        raise HTTPException(status_code=404, detail="Friend not found")
    return {"message": "Friend removed successfully"}
