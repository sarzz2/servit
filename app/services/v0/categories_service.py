import logging

from app.models.categories import CategoriesIn, CategoriesOut, CategoriesUpdate

log = logging.getLogger("fastapi")


async def create_category(server_id, name):
    """Create a new category"""
    await CategoriesIn.create_category(server_id, name)


async def get_categories(server_id: str, current_user_id):
    """Get all categories for a server, first checking cache in Redis."""
    categories = await CategoriesOut.get_categories(server_id, current_user_id)
    return categories


async def get_category_by_id(server_id: str, category_id: str):
    categories = await CategoriesOut.get_category_by_id(server_id, category_id)
    return categories


async def update_categories(server_id, category_id, name=None, position=None):
    return await CategoriesUpdate.update_category(category_id, name, position)


async def del_category(server_id, category_id):
    res = await CategoriesUpdate.delete_category(server_id, category_id)
    if res == "DELETE 0":
        raise ValueError("Minimum 1 category with a channel is required")
    return res
