from typing import Optional
from uuid import UUID

from pydantic import Field, constr

from app.core.database import DataBase


class CategoriesIn(DataBase):
    name: constr(min_length=3, max_length=255) = Field(..., description="Name of the category")

    @classmethod
    async def create_category(cls, server_id: str, name: str):
        """Create a new category"""
        query = """
                   INSERT INTO categories (server_id, name, position)
                        VALUES ($1, $2, COALESCE(
                                         (SELECT MAX(position) + 1 FROM categories WHERE server_id = $1), 1)
                                )
                """
        return await cls.execute(query, server_id, name)


class CategoriesOut(DataBase):
    id: UUID
    name: str
    position: int

    @classmethod
    async def get_categories(cls, server_id: str):
        """Get all categories for a server"""
        query = "SELECT id, name, position FROM categories WHERE server_id = $1 ORDER BY position"
        return await cls.fetch(query, server_id)


class CategoriesUpdate(DataBase):
    name: Optional[str] = Field(None, description="Name of the category")
    position: Optional[int] = Field(None, description="Position of the category")

    @classmethod
    async def update_category(cls, category_id: str, name: Optional[str] = None, position: Optional[int] = None):
        base_query = "UPDATE categories SET "
        update_fields = []
        values = []
        # Dynamically append fields to be updated
        if name is not None:
            update_fields.append("name = $1")
            values.append(name)
        if position is not None:
            update_fields.append("position = $" + str(len(values) + 1))
            values.append(position)

        # If no fields were provided, skip the update
        if not update_fields:
            raise ValueError("At least one field must be provided to update")

        # Finalize the query
        query = base_query + ", ".join(update_fields) + " WHERE id = $" + (str(len(values) + 1) + " RETURNING *")
        values.append(category_id)

        return await cls.fetchrow(query, *values)

    @classmethod
    async def delete_category(cls, server_id: str, category_id: str):
        query = "DELETE FROM categories WHERE server_id = $1 AND id = $2"
        return await cls.execute(query, server_id, category_id)
