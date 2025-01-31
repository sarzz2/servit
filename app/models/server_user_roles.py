from uuid import UUID

from app.core.database import DataBase


class ServerUserRolesIn(DataBase):
    user_id: str
    role_id: str

    @classmethod
    async def assign_role_to_user(cls, user_id: UUID, role_id: UUID, server_id: UUID):
        query = """
               SELECT EXISTS (
                   SELECT 1
                   FROM server_members
                   WHERE user_id = $1 AND server_id = $2
               );
           """
        result = await cls.fetchval(query, user_id, server_id)
        if result:
            query = """
                INSERT INTO server_user_roles
                     VALUES ($1, $2)
            """
            return await cls.execute(query, user_id, role_id)
        return False

    @classmethod
    async def remove_role_from_user(cls, user_id: UUID, role_id: UUID, server_id: UUID):
        query = """
                   SELECT EXISTS (
                       SELECT 1
                       FROM server_members
                       WHERE user_id = $1 AND server_id = $2
                   );
               """
        result = await cls.fetchval(query, user_id, server_id)
        if result:
            query = """
                    DELETE FROM server_user_roles
                          WHERE user_id = $1 AND role_id = $2
                """
            return await cls.execute(query, user_id, role_id)
        return False
