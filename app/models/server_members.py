from uuid import UUID

from pydantic import Field, constr

from app.core.database import DataBase


class ServerMembers(DataBase):
    user_id: UUID = Field(..., description="ID of the user")
    server_id: UUID = Field(..., description="ID of the server")
    nickname: constr(min_length=1, max_length=20) = Field(None, description="Nickname of the user in the server")

    @classmethod
    async def add_member(cls, user_id: str, server_id: str, nickname: str = None):
        query = """
                INSERT INTO server_members (user_id, server_id, nickname)
                VALUES ($1, $2, $3)
            """
        return await cls.execute(query, user_id, server_id, nickname)

    @classmethod
    async def remove_member(cls, user_id: str, server_id: str):
        query = """
                DELETE FROM server_members
                WHERE user_id = $1 AND server_id = $2
            """
        return await cls.execute(query, user_id, server_id)
