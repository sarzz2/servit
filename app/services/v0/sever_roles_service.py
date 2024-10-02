import logging
from uuid import UUID

from app.models.server_roles import ServerRolesIn

log = logging.getLogger("fastapi")


async def create_role(server_id: UUID, name: str, description: str, color: str):
    """
    Create a new server role.
    """
    await ServerRolesIn.new_role(server_id=server_id, name=name, description=description, color=color)
