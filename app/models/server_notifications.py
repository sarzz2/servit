from typing import List

from app.core.database import DataBase


class NotificationCounterUpdate(DataBase):
    user_id: str
    server_id: str
    channel_id: str
    unread_count: int
    mention_count: int


class BatchNotificationCounterUpdate(DataBase):
    updates: List[NotificationCounterUpdate]
