import json
import logging

from app.models.categories import CategoriesIn, CategoriesOut, CategoriesUpdate

log = logging.getLogger("fastapi")


async def create_category(server_id, name, redis):
    """Create a new category"""
    await redis.delete(f"server:{server_id}:categories")
    await CategoriesIn.create_category(server_id, name)


async def get_categories(server_id: str, redis):
    """Get all categories for a server, first checking cache in Redis."""
    cache_key = f"server:{server_id}:categories"
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # Retrieve from DB if not in cache and cache the result
    categories = await CategoriesOut.get_categories(server_id)
    categories_dict = [{**category.model_dump(), "id": str(category.id)} for category in categories]
    await redis.set(cache_key, json.dumps(categories_dict), ex=86400)
    return categories


async def get_category_by_id(server_id: str, category_id: str):
    categories = await CategoriesOut.get_category_by_id(server_id, category_id)
    return categories


async def update_categories(server_id, category_id, redis, name=None, position=None):
    await redis.delete(f"server:{server_id}:categories")
    return await CategoriesUpdate.update_category(category_id, name, position)


async def del_category(server_id, category_id, redis):
    res = await CategoriesUpdate.delete_category(server_id, category_id)
    if res == "DELETE 0":
        raise ValueError("Minimum 1 category with a channel is required")
    await redis.delete(f"server:{server_id}:categories")
    return res
