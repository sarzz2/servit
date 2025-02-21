from uuid import UUID

from pydantic import Field

from app.core.database import DataBase


class ServerPermission(DataBase):
    id: UUID = Field(..., description="ID of the permission")
    name: str = Field(..., description="Name of the permission")

    @classmethod
    async def get_permissions(cls, permission_id: str):
        query = """
            SELECT * FROM server_permissions WHERE id IN ($1);
            """
        return await cls.fetch(query, permission_id)

    @classmethod
    async def get_all_permissions(cls):
        query = """
            SELECT * FROM server_permissions;
            """
        return await cls.fetch(query)
