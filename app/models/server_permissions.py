from uuid import UUID

from pydantic import Field

from app.core.database import DataBase


class ServerPermission(DataBase):
    id: UUID = Field(..., description="ID of the permission")
    name: str = Field(..., description="Name of the permission")
