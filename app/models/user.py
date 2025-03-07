import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import UUID4, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber

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
    # Additional profile fields:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None
    profile_banner_url: Optional[str] = None

    @classmethod
    async def get_user(cls, username: str) -> dict:
        query = """
            SELECT users.id, users.username, users.email, users.profile_picture_url,
                   aud.first_name, aud.last_name, aud.date_of_birth, aud.gender, aud.phone,
                   aud.address, aud.country, aud.bio, aud.profile_banner_url
             FROM users
        LEFT JOIN additional_user_details aud ON aud.user_id = users.id
            WHERE users.id = $1;

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
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_verified: Optional[bool] = None
    profile_picture_url: Optional[str] = None
    # Additional profile fields:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    address: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None
    profile_banner_url: Optional[str] = None

    @classmethod
    async def update_user(cls, user_id: str, **kwargs):
        """
        Update the users table and upsert additional_user_details in a single query.
        This uses parameterized SQL to avoid injection and uses COALESCE to preserve
        existing values if a new value is null.
        """
        dob = kwargs.get("date_of_birth")
        if dob and isinstance(dob, str):
            dob = date.fromisoformat(dob)

        query = """
                WITH updated_user AS (
              UPDATE users
                 SET username = COALESCE($2, username), email = COALESCE($3, email),
                     profile_picture_url = COALESCE($4, profile_picture_url)
               WHERE id = $1
           RETURNING username, email, profile_picture_url, is_verified
                ),
                     upsert_profile AS (
         INSERT INTO additional_user_details (
                      user_id, first_name, last_name, date_of_birth, gender, phone,
                      address, country, bio, profile_banner_url
                     )
              VALUES ($1, $5, $6, $7, $8, $9, $10, $11, $12, $13)
         ON CONFLICT (user_id) DO UPDATE SET
                     first_name = COALESCE(EXCLUDED.first_name, additional_user_details.first_name),
                     last_name = COALESCE(EXCLUDED.last_name, additional_user_details.last_name),
                     date_of_birth = COALESCE(EXCLUDED.date_of_birth, additional_user_details.date_of_birth),
                     gender = COALESCE(EXCLUDED.gender, additional_user_details.gender),
                     phone = COALESCE(EXCLUDED.phone, additional_user_details.phone),
                     address = COALESCE(EXCLUDED.address, additional_user_details.address),
                     country = COALESCE(EXCLUDED.country, additional_user_details.country),
                     bio = COALESCE(EXCLUDED.bio, additional_user_details.bio),
                     profile_banner_url =
                        COALESCE(EXCLUDED.profile_banner_url, additional_user_details.profile_banner_url),
                     updated_at = NOW()
           RETURNING *
            )
              SELECT * FROM updated_user, upsert_profile
        """
        # Prepare parameter values in order.
        params = [
            user_id,
            kwargs.get("username"),
            kwargs.get("email"),
            kwargs.get("profile_picture_url"),
            kwargs.get("first_name"),
            kwargs.get("last_name"),
            dob,
            kwargs.get("gender"),
            kwargs.get("phone"),
            kwargs.get("address"),
            kwargs.get("country"),
            kwargs.get("bio"),
            kwargs.get("profile_banner_url"),
        ]
        return await cls.fetchrow(query, *params)


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
