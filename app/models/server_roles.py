from uuid import UUID

from pydantic import Field, constr

from app.core.database import DataBase


class ServerRolesIn(DataBase):
    name: constr(min_length=1, max_length=50) = Field(..., title="Role Name")
    description: constr(min_length=1, max_length=100) = Field(..., title="Role Description")
    color: constr(min_length=6, max_length=7) = Field("#ffffff", title="Role Color")

    @classmethod
    async def new_role(cls, server_id: UUID, name: str, description: str, color: str):
        query = """
        INSERT INTO server_roles (server_id, name, description, color)
        VALUES ($1, $2, $3, $4)
        """
        await cls.execute(query, server_id, name, description, color)


class ServerRolesOut(DataBase):
    id: UUID = Field(..., description="ID of the role")
    name: str = Field(..., description="Name of the role")
