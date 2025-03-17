import datetime
import random
import re
import string
from typing import Optional
from uuid import UUID

import asyncpg
from pydantic import Field, constr

from app.core.database import DataBase


def generate_invite_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class ServerIn(DataBase):
    name: constr(min_length=5, max_length=255) = Field(..., description="Name of the server")
    description: Optional[str] = Field(None, description="Detailed description of the server")
    is_public: bool = Field(default=True, description="Visibility of the server (public or private)")
    server_picture_url: Optional[str] = Field(None, description="URL of the server picture")

    @classmethod
    async def create_server(cls, name: str, description: str, owner_id: str, is_public: bool, server_picture_url: str):
        """Create a new server and add the owner as a member"""
        invite_code = generate_invite_code()
        # Retry logic for handling unique constraint violation
        while True:
            try:
                query = """
                            WITH inserted_server AS (
                     INSERT INTO servers (name, description, owner_id, invite_code, is_public, server_picture_url)
                          VALUES ($1, $2, $3, $4, $5, $6)
                       RETURNING id),
              inserted_config AS (
                     INSERT INTO server_config (server_id, default_notification_setting, max_members,
                                                max_categories, max_channels)
                          VALUES ((SELECT id FROM inserted_server), 'all', 10000, 50, 100)
                       RETURNING server_id
                                 ),
              inserted_member AS (
                     INSERT INTO server_members (server_id, user_id, nickname)
                          VALUES ((SELECT id FROM inserted_server), $3, null)
                       RETURNING server_id),
                inserted_role AS (
                     INSERT INTO server_roles (server_id, name, description, color)
                          VALUES (
                                    (SELECT server_id FROM inserted_member),
                                    '@everyone',
                                    'Default role for all members',
                                    '#000000'
                                 )
                       RETURNING id),
          default_permissions AS (
                          SELECT id FROM server_permissions
                           WHERE name IN (
                                            'VIEW_CHANNEL',
                                            'SEND_MESSAGES',
                                            'READ_MESSAGE_HISTORY',
                                            'SPEAK',
                                            'CHANGE_NICKNAME'
                                         )
                                 ),
    inserted_server_role_perm AS (
                     INSERT INTO server_role_permissions (role_id, permission_id)
                          SELECT (SELECT id FROM inserted_role), id
                            FROM default_permissions
                       RETURNING role_id
                                ),
            inserted_category AS (
                     INSERT INTO categories (server_id, name, position)
                          VALUES ((SELECT id FROM inserted_server), 'general', 1)
                       RETURNING id
                                 ),
             inserted_channel AS (
                     INSERT INTO channels (server_id, category_id, name, description, position)
                          VALUES (
                                   (SELECT id FROM inserted_server),
                                    (SELECT id FROM inserted_category),
                                    'general',
                                    'general',
                                    1
                                  )
                       RETURNING id)
                     INSERT INTO server_user_roles (user_id, role_id)
                          VALUES ($3, (SELECT id FROM inserted_role));
                    """
                # Try executing the insert query with the generated invite code
                return await cls.execute(query, name, description, owner_id, invite_code, is_public, server_picture_url)
            except asyncpg.UniqueViolationError as e:
                constraint_name = re.search(r"Key \((.*?)\)=\((.*?)\) already exists", str(e), re.IGNORECASE).group(1)
                if constraint_name != "invite_code":
                    raise e
                invite_code = cls.generate_invite_code()


class ServerOut(DataBase):
    id: UUID = Field(..., description="ID of the server")
    owner_id: UUID = Field(..., description="ID of the owner (must match a user UUID)")
    name: constr(max_length=255) = Field(..., description="Name of the server")
    description: Optional[str] = Field(None, description="Detailed description of the server")
    invite_code: constr(max_length=20) = Field(..., description="Unique invite code for the server")
    is_public: bool = Field(..., description="Visibility of the server (public or private)")
    max_members: int = Field(..., description="Maximum number of members allowed in the server")
    server_picture_url: Optional[str] = Field(None, description="URL of the server picture")
    created_at: datetime.datetime = Field(..., description="Date and time of server creation")
    default_notification_setting: Optional[str] = None

    @classmethod
    async def get_server_by_invite_code(cls, invite_code: str):
        query = """
                SELECT * FROM servers
                WHERE invite_code = $1
            """
        return await cls.fetchrow(query, invite_code)

    @classmethod
    async def get_server_by_id(cls, id: str):
        query = """
                SELECT s.*, sc.default_notification_setting FROM servers s
            INNER JOIN server_config sc on s.id = sc.server_id
                 WHERE id = $1
            """
        return await cls.fetchrow(query, id)

    @classmethod
    async def get_all_user_servers(cls, user_id):
        query = """
                SELECT * FROM servers s
                JOIN server_members sm ON s.id = sm.server_id
                WHERE sm.user_id = $1 AND sm.deleted_at IS NULL
            """
        return await cls.fetch(query, user_id)


class ServerUpdate(DataBase):
    name: Optional[constr(min_length=5, max_length=255)] = Field(None, description="Name of the server")
    description: Optional[str] = Field(None, description="Detailed description of the server")
    is_public: Optional[bool] = Field(None, description="Visibility of the server (public or private)")
    owner_id: Optional[UUID] = Field(None, description="ID of the owner (must match a user UUID)")
    server_picture_url: Optional[str] = Field(None, description="URL of the server picture")
    invite_code: Optional[constr(min_length=6, max_length=20)] = Field(
        None, description="Unique invite code for the server"
    )

    @classmethod
    async def update_server(cls, server_id: str, **kwargs):
        """Update server details"""
        # Construct the SET clause dynamically
        for key in kwargs:
            if isinstance(kwargs[key], int) and key in {"is_public"}:
                kwargs[key] = bool(kwargs[key])
        set_clause = ", ".join([f"{key} = ${i + 2}" for i, key in enumerate(kwargs.keys())])
        query = f"""
                UPDATE servers
                SET {set_clause}
                WHERE id = $1;
            """
        values = list(kwargs.values())
        return await cls.execute(query, server_id, *values)

    @classmethod
    async def regenerate_invite_code(cls, server_id):
        invite_code = generate_invite_code()
        query = """UPDATE servers SET invite_code = $1 WHERE id = $2"""
        while True:
            try:
                await cls.fetchval(query, invite_code, server_id)
                return invite_code
            except asyncpg.UniqueViolationError:
                invite_code = cls.generate_invite_code()
