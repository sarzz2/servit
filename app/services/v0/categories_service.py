import logging

from app.models.categories import CategoriesIn, CategoriesOut, CategoriesUpdate

log = logging.getLogger("fastapi")


async def create_category(server_id, name):
    """Create a new category"""
    await CategoriesIn.create_category(server_id, name)


async def get_categories(server_id):
    """Get all categories for a server"""
    return await CategoriesOut.get_categories(server_id)


async def update_categories(category_id, name=None, position=None):
    return await CategoriesUpdate.update_category(category_id, name, position)
