import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis
from starlette import status
from starlette.responses import JSONResponse

from app import constants
from app.api.v0.routers import limiter
from app.core.dependencies import get_current_user, get_redis
from app.models.categories import CategoriesIn, CategoriesUpdate
from app.models.user import UserModel
from app.services.v0.audit_log_service import insert_audit_log
from app.services.v0.categories_service import (
    create_category,
    del_category,
    get_categories,
    get_category_by_id,
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
    await insert_audit_log(
        user_id=current_user["id"],
        entity="category",
        entity_id=server_id,
        action=constants.CREATE,
        changes=json.dumps({"action": f"{current_user['username']} created new category {category.name}"}),
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
    # Fetch the existing category to log changes
    try:
        existing_category = (await get_category_by_id(server_id, category_id)).model_dump()
        update_data = await request.json()

        # Update the category
        result = await update_categories(server_id, category_id, redis, category.name, category.position)

        changes = {
            key: {"before": existing_category[key], "after": value}
            for key, value in update_data.items()
            if existing_category.get(key) != value
        }

        if changes:
            await insert_audit_log(
                user_id=current_user["id"],
                entity="category",
                entity_id=server_id,
                action=constants.UPDATE,
                changes=json.dumps(changes),
            )

        return result
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


@router.delete("/{server_id}/{category_id}")
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
async def delete_category(
    server_id: str,
    category_id: str,
    current_user: UserModel = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    try:
        category = (await get_category_by_id(server_id, category_id)).model_dump()
        result = await del_category(server_id, category_id, redis)
        await insert_audit_log(
            user_id=current_user["id"],
            entity="category",
            entity_id=server_id,
            action=constants.DELETE,
            changes=json.dumps({"action": f"{current_user['username']} deleted category {category['name']}"}),
        )
        return result
    except Exception:
        return JSONResponse({"error": "Category does not exist"}, status_code=status.HTTP_400_BAD_REQUEST)
