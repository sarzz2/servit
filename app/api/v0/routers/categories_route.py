import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.core.dependencies import get_current_user
from app.models.categories import CategoriesIn, CategoriesUpdate
from app.models.user import UserModel
from app.services.v0.categories_service import create_category, get_categories, update_categories, del_category
from app.services.v0.permission_service import check_permissions

router = APIRouter(dependencies=[Depends(get_current_user)])
log = logging.getLogger("fastapi")


@router.post("/{server_id}", status_code=status.HTTP_201_CREATED)
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
async def create_new_category(
        server_id: str,
        category: CategoriesIn,
        current_user: UserModel = Depends(get_current_user),
):
    """Create a new category"""
    try:
        await create_category(
            server_id=server_id,
            name=category.name,
        )
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid server_id",
        )
    log.info(
        f"Category created successfully: {category.name} by Username:{current_user['username']} & Id {current_user['id']}"
    )
    return {"message": "Category created successfully", "category": category.model_dump()}


@router.get("/{server_id}")
async def get_server_categories(server_id: str):
    """Get all categories for a server"""
    result = await get_categories(server_id)
    return result


@router.patch("/{server_id}/{category_id}")
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
async def update_category(
        server_id: str,
        category_id: str,
        category: CategoriesUpdate,
        current_user: UserModel = Depends(get_current_user)
):
    result = await update_categories(category_id, name=category.name, position=category.position)
    return result


@router.delete("/{server_id}/{category_id}")
@check_permissions(["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"])
async def delete_category(server_id: str, category_id: str, current_user: UserModel = Depends(get_current_user)):
    required_permissions = ["MANAGE_CHANNELS", "MANAGE_SERVER", "ADMINISTRATOR"]
    result = await del_category(server_id, category_id)
    return result
