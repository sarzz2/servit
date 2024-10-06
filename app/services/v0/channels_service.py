from app.models.channels import ChannelIn, ChannelOut, ChannelUpdate


async def create_channel(server_id: str, category_id: str, name: str, description: str):
    """Create a new channel"""
    return await ChannelIn.create_channel(server_id, category_id, name, description)


async def get_channels(server_id: str, category_id: str):
    """Get all channels for a category"""
    return await ChannelOut.get_channels(server_id, category_id)


async def update_channel(channel_id: str, name: str, description: str, position: int):
    """Update a channel"""
    return await ChannelUpdate.update_channel(channel_id, name, description, position)


async def del_channel(server_id: str, channel_id: str):
    """Delete a channel"""
    return await ChannelUpdate.del_channel(server_id, channel_id)
