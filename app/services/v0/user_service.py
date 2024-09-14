import logging
from typing import Optional

from app.core.auth import verify_password
from app.models.user import UserIn, UserLogin

log = logging.getLogger("fastapi")


async def register_user(username: str, email: str, password: str) -> dict:
    return await UserIn.create_user(username, email, password)


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = await UserLogin.get_user_by_username(username=username)
    if user and verify_password(password, user["password"]):
        return user
    return None
