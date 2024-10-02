import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends
from starlette import status

from app.core.dependencies import get_current_user
from app.models.server_roles import ServerRolesIn
from app.services.v0.sever_roles_service import create_role

router = APIRouter(dependencies=[Depends(get_current_user)])
log = logging.getLogger("fastapi")


@router.post("/{server_id}", status_code=status.HTTP_201_CREATED)
async def create_server_role(server_id: UUID, server_role: ServerRolesIn):
    """
    Create a new server role.
    """
    try:
        await create_role(server_id, **server_role.model_dump())
        return {"message": "Role created successfully", "role": server_role.model_dump()}
    except asyncpg.exceptions.UniqueViolationError as e:
        log.error(f"Failed to create server role: {e}")
        return {"error": "Role with this name already exists."}
