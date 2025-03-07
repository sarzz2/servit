from uuid import UUID

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
