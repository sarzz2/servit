from datetime import datetime
from typing import Optional

from pydantic import UUID4, EmailStr

from app.core.database import DataBase


class StaffLogin(DataBase):
    id: Optional[UUID4] = None
    role: Optional[str] = None
    email: EmailStr
    password: str

    @classmethod
    async def get_staff_by_email(cls, email: EmailStr):
        query = """
        SELECT * FROM staff WHERE email = $1
        """
        return await cls.fetchrow(query, email)


class StaffCreate(DataBase):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str
    password: str

    @classmethod
    async def create_staff(cls, name: str, email: EmailStr, phone: Optional[str], role: str, password: str):
        query = """
        INSERT INTO staff (name, email, phone, role, password)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT DO NOTHING
        RETURNING *;
        """
        return await cls.execute(query, name, email, phone, role, password)


class StaffUpdate(DataBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

    @classmethod
    async def update_staff(cls, staff_id: str, staff):
        query = """
        UPDATE staff
SET name = COALESCE($1, name), email = COALESCE($2, email), phone = COALESCE($3, phone), role = COALESCE($4, role)
WHERE id = $5
        """
        return await cls.execute(query, staff.name, staff.email, staff.phone, staff.role, staff_id)

    @classmethod
    async def delete_staff(cls, staff_id):
        query = """
        UPDATE staff SET deleted_at = NOW() WHERE id = $1
        """
        return await cls.execute(query, staff_id)


class StaffOut(DataBase):
    id: Optional[UUID4] = None
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()

    @classmethod
    async def get_staff(cls):
        query = """
        SELECT id, name, email, phone, role, created_at, updated_at FROM staff
        """
        return await cls.fetch(query)

    @classmethod
    async def get_staff_by_id(cls, staff_id: str):
        query = """
        SELECT id, name, email, phone, role, created_at, updated_at FROM staff WHERE id = $1
        """
        return await cls.fetchrow(query, staff_id)
