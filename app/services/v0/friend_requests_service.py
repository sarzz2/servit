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
    async def get_all_friends(user_id: UUID):
        return await FriendRequest.get_friends(user_id)

    @staticmethod
    async def get_pending_requests(user_id: UUID):
        return await FriendRequest.get_friend_requests(user_id)

    @staticmethod
    async def remove_friend(user_id: UUID, friend_id: UUID):
        return await FriendRequest.remove_friend(user_id, friend_id)
