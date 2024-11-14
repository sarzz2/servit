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
        INSERT INTO server_members AS sm (user_id, server_id, nickname)
             VALUES ($1, $2, $3)
        ON CONFLICT (user_id, server_id) DO
         UPDATE SET deleted_at = NULL
              WHERE sm.server_id = $2 AND sm.user_id = $1 AND sm.deleted_at IS NOT NULL
          RETURNING *

        """
        return await cls.execute(query, user_id, server_id, nickname)

    @classmethod
    async def remove_member(cls, user_id: str, server_id: str):
        async with cls.pool.acquire() as connection:  # Acquire a connection from the pool
            async with connection.transaction():  # Start a transaction
                # Check if the user is the owner of the server
                owner_id = await cls.fetchval(
                    """
                    SELECT owner_id FROM servers
                    WHERE id = $1
                """,
                    server_id,
                    con=connection,
                )

                if owner_id == user_id:
                    await cls.execute(
                        """
                        DELETE FROM servers
                        WHERE id = $1
                    """,
                        server_id,
                        con=connection,
                    )

                    await cls.execute(
                        """
                        DELETE FROM server_members
                        WHERE server_id = $1
                    """,
                        server_id,
                        con=connection,
                    )

                    await cls.execute(
                        """
                        DELETE FROM server_user_roles
                        WHERE role_id IN (
                            SELECT id FROM server_roles
                            WHERE server_id = $1
                        )
                    """,
                        server_id,
                        con=connection,
                    )

                    await cls.execute(
                        """
                        DELETE FROM server_roles
                        WHERE server_id = $1
                    """,
                        server_id,
                        con=connection,
                    )

                else:
                    # Soft delete from server_members
                    query = """
                            UPDATE server_members
                               SET deleted_at = NOW()
                             WHERE server_id = $1 AND user_id = $2 AND deleted_at IS NULL
                    """
                    await cls.execute(query, server_id, user_id, con=connection)
