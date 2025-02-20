from typing import Optional
from uuid import UUID

from pydantic import Field, constr

from app.core.database import DataBase


class ChannelIn(DataBase):
    id: Optional[UUID] = None
    name: constr(min_length=3, max_length=100) = Field(default=..., description="Channel name")
    description: Optional[constr(min_length=3, max_length=255)] = Field(default=None, description="Channel description")

    @classmethod
    async def create_channel(cls, server_id: str, category_id: str, name: str, description: Optional[str] = None):
        """Create a new channel with category and server validation."""
        query = """
                WITH category_check AS (
              SELECT 1 FROM categories WHERE id = $2 AND server_id = $1
                )
         INSERT INTO channels (server_id, category_id, name, position, description)
              SELECT $1, $2, $3, COALESCE(
                                 (SELECT MAX(position) + 1 FROM channels WHERE server_id = $1 AND category_id = $2), 1
                ), $4
        WHERE EXISTS (SELECT 1 FROM category_check)
           RETURNING id, name, position, category_id, server_id, description
            """
        return await cls.fetchrow(query, server_id, category_id, name, description)


class ChannelOut(DataBase):
    id: UUID
    name: str
    position: int
    description: Optional[str] = None
    category_id: UUID
    server_id: UUID

    @classmethod
    async def get_channels(cls, server_id: str, category_id: str):
        """Get all channels for a category."""
        query = """
                    SELECT id, name, position, description, category_id, server_id FROM channels
                     WHERE server_id = $1 AND category_id = $2
                  ORDER BY position
                """
        return await cls.fetch(query, server_id, category_id)

    @classmethod
    async def get_channel(cls, channel_id: str):
        """Get Channel from its ID"""
        query = """
            SELECT * FROM channels WHERE id = $1
        """
        return await cls.fetchrow(query, channel_id)


class ChannelUpdate(DataBase):
    name: constr(min_length=3, max_length=100) = Field(None, description="Channel name")
    description: constr(min_length=3, max_length=100) = Field(None, description="Channel description")
    position: Optional[int] = Field(None, description="Channel position")

    @classmethod
    async def update_channel(
        cls,
        channel_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        position: Optional[int] = None,
    ):
        """Update a channel."""
        base_query = "UPDATE channels SET "
        update_fields = []
        values = []
        # Dynamically append fields to be updated
        if name is not None:
            update_fields.append("name = $1")
            values.append(name)
        if position is not None:
            update_fields.append("position = $" + str(len(values) + 1))
            values.append(position)
        if description is not None:
            update_fields.append("description = $" + str(len(values) + 1))
            values.append(description)

        # If no fields were provided, skip the update
        if not update_fields:
            raise ValueError("At least one field must be provided to update")

        # Finalize the query
        query = base_query + ", ".join(update_fields) + " WHERE id = $" + (str(len(values) + 1) + " RETURNING *")
        values.append(channel_id)
        return await cls.fetchrow(query, *values)

    @classmethod
    async def del_channel(cls, server_id: str, channel_id: str):
        """Delete a channel."""
        query = "DELETE FROM channels WHERE server_id = $1 AND id = $2"
        result = await cls.execute(query, server_id, channel_id)
        if result == "DELETE 1":
            return result
        return None
