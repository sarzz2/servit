from typing import List
from uuid import UUID

from pydantic import Field

from app.core.database import DataBase


class ServerRolePermission(DataBase):
    # role_id: UUID = Field(...)
    permission_id: List[UUID] = Field(...)

    @classmethod
    async def assign_permission(cls, server_id, user_id, permission_id):
        query = """
           INSERT INTO server_user_permissions (user_id, permission_id)
                SELECT $2, unnest($3::uuid[])
                  FROM server_members
                 WHERE server_id = $1 AND user_id = $2
             RETURNING user_id, permission_id;
           """
        result = await cls.execute(query, server_id, user_id, permission_id)
        if result == "INSERT 0 0":
            raise ValueError("The specified user does not belong to the server.")
        return result

    @classmethod
    async def remove_permission(cls, server_id, user_id, permission_ids: List[UUID]):
        query = """
        DELETE FROM server_user_permissions
              WHERE user_id = $2
                AND permission_id = ANY($3::uuid[])
         AND EXISTS (
             SELECT 1
               FROM server_members
              WHERE server_id = $1 AND user_id = $2
          )
          RETURNING user_id, permission_id;
        """
        result = await cls.execute(query, server_id, user_id, permission_ids)
        print(result)
        if result == "DELETE 0":
            raise ValueError("The specified user does not belong to the server or the permissions do not exist.")
        return result
