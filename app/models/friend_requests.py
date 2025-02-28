from typing import Optional
from uuid import UUID

from app.core.database import DataBase


class FriendRequest(DataBase):
    user_id: UUID
    friend_id: UUID
    status: str
    profile_picture_url: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None

    @classmethod
    async def add_friend(cls, user_id: UUID, friend_id: UUID):
        query = """
            INSERT INTO friends (user_id, friend_id, status)
            VALUES ($1, $2, 'pending')
            RETURNING *;
        """
        return await cls.execute(query, user_id, friend_id)

    @classmethod
    async def update_status(cls, friend_id: UUID, user_id: UUID, status: str):
        query = """
            UPDATE friends
            SET status = $1, updated_at = NOW()
            WHERE user_id = $2 AND friend_id = $3
            RETURNING *;
        """
        return await cls.fetchrow(query, status, user_id, friend_id)

    @classmethod
    async def get_friends(cls, user_id: UUID, search_query: str, page: int, per_page: int):
        query = """
            SELECT
              CASE WHEN friends.user_id = $1
                   THEN u2.username
                   ELSE u1.username
                    END AS username,
              CASE WHEN friends.user_id = $1
                   THEN u2.email
                   ELSE u1.email
                 END AS email,
              CASE WHEN friends.user_id = $1
                   THEN u2.profile_picture_url
                   ELSE u1.profile_picture_url
                    END AS profile_picture_url,
                        friends.status, friends.user_id, friends.friend_id
                   FROM friends
                   JOIN users u1 ON friends.user_id = u1.id
                   JOIN users u2 ON friends.friend_id = u2.id
                  WHERE (friends.user_id = $1 OR friends.friend_id = $1) AND status = 'accepted'
                    AND (
                       $2::text IS NULL
                       OR $2::text = ''
                       OR (CASE WHEN friends.user_id = $1 THEN u2.username
                                ELSE u1.username END) ILIKE '%' || $2::text || '%'
                            )
                  LIMIT $3 OFFSET $4;
            """
        offset = (page - 1) * per_page
        return await cls.fetch(query, user_id, search_query, per_page, offset)

    @classmethod
    async def get_friend_requests(cls, user_id: UUID, search_query: str, page: int, per_page: int):
        query = """
            SELECT user_id, friend_id, status, username, email, profile_picture_url FROM friends
              JOIN users ON friends.user_id = users.id
             WHERE friend_id = $1 AND status = 'pending'
                   AND (
                       $2::text IS NULL
                       OR $2::text = ''
                       OR users.username ILIKE '%' || $2::text || '%'
                      )
          ORDER BY friends.created_at DESC
             LIMIT $3 OFFSET $4;
        """
        offset = (page - 1) * per_page
        return await cls.fetch(query, user_id, search_query, per_page, offset)

    @classmethod
    async def get_blocked_friends(cls, user_id: UUID, search_query: str, page: int, per_page: int):
        query = """
            SELECT user_id, friend_id, status, username, email, profile_picture_url FROM friends
              JOIN users ON friends.user_id = users.id
             WHERE friend_id = $1 AND status = 'blocked'
                    AND (
                       $2::text IS NULL
                       OR $2::text = ''
                       OR users.username ILIKE '%' || $2::text || '%'
                      )
          ORDER BY friends.created_at DESC
             LIMIT $3 OFFSET $4;
        """
        offset = (page - 1) * per_page
        return await cls.fetch(query, user_id, search_query, page, offset)

    @classmethod
    async def remove_friend(cls, user_id: UUID, friend_id: UUID):
        query = """
            DELETE FROM friends
            WHERE user_id = $1 AND friend_id = $2 OR user_id = $2 AND friend_id = $1
            RETURNING *;
        """
        return await cls.fetchrow(query, user_id, friend_id)

    @classmethod
    async def delete_request(cls, user_id: UUID, friend_id: UUID):
        query = """
            DELETE FROM friends
            WHERE user_id = $1 AND friend_id = $2
        """
        return await cls.execute(query, user_id, friend_id)
