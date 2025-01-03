import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis
from starlette import status

from app.api.v0.routers import limiter
from app.core.dependencies import get_current_user, get_redis
from app.models.categories import CategoriesIn, CategoriesUpdate
from app.models.user import UserModel
from app.services.v0.categories_service import (
    create_category,
    del_category,
    get_categories,
    update_categories,
)
from app.services.v0.permission_service import check_permissions

router = APIRouter(dependencies=[Depends(get_current_user)])
log = logging.getLogger("fastapi")


@router.post("/{server_id}", status_code=status.HTTP_201_CREATED)
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
@limiter.limit("10/minute")
async def create_new_category(
    request: Request,
    server_id: str,
    category: CategoriesIn,
    current_user: UserModel = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    """Create a new category"""
    await create_category(server_id=server_id, name=category.name, redis=redis)
    log.info(
        f"Category created successfully: {category.name} by Username:{current_user['username']}"
        f" & Id {current_user['id']}"
    )
    return {"message": "Category created successfully", "category": category.model_dump()}


@router.get("/{server_id}")
async def get_server_categories(server_id: str, redis: Redis = Depends(get_redis)):
    """Get all categories for a server, using Redis cache."""
    result = await get_categories(server_id, redis)
    return result


@router.patch("/{server_id}/{category_id}")
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
async def update_category(
    request: Request,
    server_id: str,
    category_id: str,
    category: CategoriesUpdate,
    current_user: UserModel = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    result = await update_categories(server_id, category_id, redis, category.name, category.position)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return result


@router.delete("/{server_id}/{category_id}")
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
async def delete_category(
    server_id: str,
    category_id: str,
    current_user: UserModel = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    result = await del_category(server_id, category_id, redis)
    return result
