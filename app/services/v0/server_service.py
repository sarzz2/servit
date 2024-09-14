import logging

from app.models.server import ServerOut, ServerUpdate, ServerIn
from app.models.server_members import ServerMembers

log = logging.getLogger("fastapi")


async def create_server(current_user, name: str, description: str, is_public: bool = False):
    return await ServerIn.create_server(name, description, current_user["id"], is_public)


async def get_server_details_by_id(server_id: str):
    return await ServerOut.get_server_by_name(server_id)


async def join_server(invite_link: str, current_user):
    server = await ServerOut.get_server_by_invite_code(invite_link)
    if server is None:
        return None
    await ServerMembers.add_member(user_id=current_user["id"], server_id=server.id)
    return server


async def leave_server(server_id: str, current_user):
    return await ServerMembers.remove_member(user_id=current_user, server_id=server_id)


async def update_server(server_id: str, **kwargs):
    return await ServerUpdate.update_server(server_id, **kwargs)
