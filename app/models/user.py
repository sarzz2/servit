import uuid
from typing import Optional

from pydantic import UUID4, EmailStr, Field

from app.core.auth import get_password_hash
from app.core.database import DataBase


class UserIn(DataBase):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8)
    profile_picture_url: Optional[str] = Field(default=None)

    @classmethod
    async def create_user(cls, username: str, email: str, password: str):
        query = """
            INSERT INTO users (username, email, password)
                 VALUES ($1, $2, $3);
        """
        return await cls.execute(query, username, email, get_password_hash(password))


class UserLogin(DataBase):
    id: Optional[UUID4] = None
    username: str
    password: str

    @classmethod
    async def get_user_by_username(cls, username: str) -> dict:
        query = """
            SELECT id, username, email, password
            FROM users
            WHERE username = $1;
        """
        user = await cls.fetchrow(query, username)
        return dict(user) if user else None


class UserModel(DataBase):
    id: UUID4
    username: str
    email: EmailStr
    profile_picture_url: Optional[str]
    status: Optional[str] = None

    @classmethod
    async def get_user(cls, username: str) -> dict:
        query = """
            SELECT id, username, email, profile_picture_url
              FROM users
            WHERE id = $1;
        """
        user = await cls.fetchrow(query, username)
        return dict(user) if user else None

    @classmethod
    async def get_users(cls, user_id: str) -> dict:
        query = """
                SELECT id, username, email, profile_picture_url
                  FROM users
                 WHERE id IN ($1);
            """
        user = await cls.fetchrow(query, user_id)
        return dict(user) if user else None

    @classmethod
    async def search_user(cls, term: str, current_user: UUID4):
        query = """
                SELECT u.id, u.username, u.email, u.profile_picture_url, fr.status
                  FROM users u
                  LEFT JOIN friends fr
                    ON (fr.user_id = $2 AND fr.friend_id = u.id)
                    OR (fr.user_id = u.id AND fr.friend_id = $2)
                 WHERE (u.username ILIKE '%' || $1 || '%'
                    OR u.email ILIKE '%' || $1 || '%')
                   AND u.id != $2  -- Exclude the user performing the search
                   AND (fr.status IS NULL OR fr.status != 'blocked') -- Exclude blocked users
                 LIMIT 15;
        """
        users = await cls.fetch(query, term, current_user)
        if users:
            return [dict(user) for user in users]
        return {"message": "No user found"}


class SudoUserModel(UserModel):
    password: str

    @classmethod
    async def get_user(cls, username: str) -> dict:
        query = """
                  SELECT *
                    FROM users
                  WHERE id = $1;
              """
        user = await cls.fetchrow(query, username)
        return dict(user) if user else None


class UserUpdate(DataBase):
    username: Optional[str]
    email: Optional[EmailStr]
    profile_picture_url: Optional[str]

    @classmethod
    async def update_user(cls, user_id: str, **kwargs):
        """Update user details"""
        # Construct the SET clause dynamically
        set_clause = ", ".join([f"{key} = ${i + 2}" for i, key in enumerate(kwargs.keys())])
        query = f"""
                UPDATE users SET {set_clause}
                 WHERE id = $1
             RETURNING *;
            """
        values = list(kwargs.values())
        return await cls.fetchrow(query, user_id, *values)


class ChangePassword(DataBase):
    new_password: str
    current_password: str

    @classmethod
    async def change_password(cls, new_password: str, user_id: str):
        query = """
            UPDATE users SET password = $1
             WHERE id = $2
            """
        return await cls.execute(query, new_password, user_id)
