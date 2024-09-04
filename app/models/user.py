from pydantic import BaseModel, EmailStr

from app.core.auth import get_password_hash
from app.core.database import DataBase


class UserLogin(DataBase):
    username: str
    password: str

    @classmethod
    async def get_user_by_username(cls, username: str) -> dict:
        query = """
            SELECT username, email, password
            FROM users
            WHERE username = $1;
        """
        user = await cls.fetchrow(query, username)
        return dict(user) if user else None



class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserModel(DataBase):
    username: str
    email: EmailStr

    @classmethod
    async def create_user(cls, username: str, email: str, password: str):
        query = """
            INSERT INTO users (username, email, password)
            VALUES ($1, $2, $3);
        """
        return await cls.execute(query, username, email, get_password_hash(password))
