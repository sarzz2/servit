import json

from app.models.channels import ChannelIn, ChannelOut, ChannelUpdate


async def create_channel(server_id: str, category_id: str, name: str, description: str, redis):
    """Create a new channel"""
    await redis.delete(f"server:{server_id}:channels")
    return await ChannelIn.create_channel(server_id, category_id, name, description)


async def get_channels(server_id: str, category_id: str, redis):
    """Get all channels for a category"""
    cache_key = f"server:{server_id}:channels"
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    result = await ChannelOut.get_channels(server_id, category_id)
    serializable_result = [channel.model_dump() for channel in result]
    await redis.set(cache_key, json.dumps(serializable_result, default=lambda o: str(o)), ex=86400)
    return result


async def update_channel(channel_id: str, server_id: str, name: str, description: str, position: int, redis):
    """Update a channel"""
    await redis.delete(f"server:{server_id}:channels")
    return await ChannelUpdate.update_channel(channel_id, name, description, position)


async def del_channel(server_id: str, channel_id: str, redis):
    """Delete a channel"""
    result = await ChannelUpdate.del_channel(server_id, channel_id)
    if result == "DELETE 0":
        raise ValueError("Minimum 1 channel is required")
    await redis.delete(f"server:{server_id}:channels")
    return result
