import logging
from typing import Optional

from app.core.auth import get_password_hash, verify_password
from app.models.user import ChangePassword, UserIn, UserLogin

log = logging.getLogger("fastapi")


async def register_user(username: str, email: str, password: str) -> dict:
    return await UserIn.create_user(username, email, password)


async def verify_user(username: str):
    return await UserIn.verify_user(username)


async def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = await UserLogin.get_user_by_username(username=username)
    if user and verify_password(password, user["password"]):
        return user
    return None


async def update_user_password(password: str, user_id: str):
    return await ChangePassword.change_password(get_password_hash(password), user_id)
