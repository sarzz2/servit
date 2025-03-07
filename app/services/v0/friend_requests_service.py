from uuid import UUID

from app.core.database import DataBase
from app.models.friend_requests import FriendRequest


class FriendService:
    @staticmethod
    async def send_friend_request(user_id: UUID, friend_id: UUID):
        return await FriendRequest.add_friend(user_id, friend_id)

    @staticmethod
    async def update_friend_status(user_id: UUID, friend_id: UUID, status: str):
        return await FriendRequest.update_status(user_id, friend_id, status)

    @staticmethod
    async def get_all_friends(user_id: UUID, search_query: str, page: int = 1, per_page: int = 25):
        return await FriendRequest.get_friends(user_id, search_query, page, per_page)

    @staticmethod
    async def get_pending_requests(user_id: UUID, search_query: str, page: int = 1, per_page: int = 25):
        return await FriendRequest.get_friend_requests(user_id, search_query, page, per_page)

    @staticmethod
    async def remove_friend(user_id: UUID, friend_id: UUID):
        return await FriendRequest.remove_friend(user_id, friend_id)

    @staticmethod
    async def get_blocked_friends(user_id: UUID, search_query: str, page: int = 1, per_page: int = 25):
        return await FriendRequest.get_blocked_friends(user_id, search_query, page, per_page)

    @staticmethod
    async def cancel_request(user_id: UUID, friend_id: UUID):
        return await FriendRequest.delete_request(user_id, friend_id)

    @staticmethod
    async def get_mutual_friends(current_user_id: UUID, user_id: UUID):
        query = """
               WITH user1_friends AS (
             SELECT CASE
                    WHEN user_id = $1 THEN friend_id
                    ELSE user_id
                    END AS friend_id
               FROM friends
              WHERE (user_id = $1 OR friend_id = $1)
                AND status = 'accepted'
                ),
   user2_friends AS (
             SELECT CASE
                    WHEN user_id = $2 THEN friend_id
                    ELSE user_id
                    END AS friend_id
               FROM friends
              WHERE (user_id = $2 OR friend_id = $2)
                AND status = 'accepted'
            )
             SELECT u.*
               FROM user1_friends uf
               JOIN user2_friends uf2 ON uf.friend_id = uf2.friend_id
               JOIN users u ON u.id = uf.friend_id;
        """
        return await DataBase.fetch(query, current_user_id, user_id)
