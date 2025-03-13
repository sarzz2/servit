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
    async def get_categories(cls, server_id: str, current_user_id: str):
        """Get all categories for a server"""
        query = """
            SELECT DISTINCT c.id, c.name, c.position FROM categories c
              JOIN servers s ON c.server_id = s.id
             WHERE c.server_id = $1
               AND (
                -- If user is the server owner, show all categories.
                    s.owner_id = $2
                OR
                -- If user holds a role with the "ADMINISTRATOR" permission in this server.
            EXISTS (
            SELECT 1
              FROM server_user_roles sur
              JOIN server_roles sr ON sur.role_id = sr.id
              JOIN server_role_permissions srp ON sur.role_id = srp.role_id
              JOIN server_permissions sp ON srp.permission_id = sp.id
             WHERE sur.user_id = $2 AND sr.server_id = $1 AND sp.name = 'ADMINISTRATOR'
                   )
                OR (
                  -- Otherwise, show the category if it is not restricted...
        NOT EXISTS (
            SELECT 1
              FROM category_role_assignments cra
             WHERE cra.category_id = c.id
                   )
                OR
                  -- ...or if it is restricted, ensure the user holds one of the required roles.
            EXISTS (
            SELECT 1
              FROM category_role_assignments cra
             WHERE cra.category_id = c.id
               AND cra.role_id IN (
                           SELECT sur.role_id FROM server_user_roles sur
                             JOIN server_roles sr ON sur.role_id = sr.id
                            WHERE sur.user_id = $2 AND sr.server_id = $1
                      )
                  )
                )
              )
          ORDER BY c.position;
        """
        return await cls.fetch(query, server_id, current_user_id)

    @classmethod
    async def get_category_by_id(cls, server_id: str, category_id: str):
        """Get all categories for a server"""
        query = "SELECT id, name, position FROM categories WHERE server_id = $1 and id = $2"
        return await cls.fetchrow(query, server_id, category_id)


class CategoriesUpdate(DataBase):
    name: constr(min_length=3, max_length=255) = Field(None, description="Name of the category")
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
        query = """
        DELETE FROM categories WHERE server_id = $1 AND id = $2
                AND (SELECT COUNT(*) FROM categories WHERE server_id = $1) > 1
                AND (SELECT COUNT(*) FROM channels WHERE server_id = $1) > 1;
        """
        return await cls.execute(query, server_id, category_id)
