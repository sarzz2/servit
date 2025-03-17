from app.core.database import DataBase


async def get_notification_preference(redis, user_id: str, server_id: str):
    cache_key = f"notification_preference:{server_id}:{user_id}"
    cached_preference = await redis.get(cache_key)
    if cached_preference:
        return cached_preference

    # If not cached, fetch from the database
    query = """
          SELECT notification_preference
            FROM server_notification_settings
           WHERE user_id = $1 AND server_id = $2;
      """
    result = await DataBase.fetchval(query, user_id, server_id)

    if result is None:
        # If no custom record, use the server's default from the config table
        query = """
                   SELECT default_notification_setting
                     FROM server_config
                    WHERE server_id = $1;
               """
        result = await DataBase.fetchval(query, server_id)
        return result
    await redis.set(cache_key, result)
    return result


async def update_notification_preference(redis, user_id: str, server_id: str, notification_preference: str):
    cache_key = f"notification_preference:{server_id}:{user_id}"
    await redis.delete(cache_key)
    # Fetch server config to get its default notification setting
    config_query = """
          SELECT default_notification_setting
            FROM server_config
           WHERE server_id = $1;
      """
    default_pref = await DataBase.fetchval(config_query, server_id)

    # If user is setting to the default, delete any custom record
    if notification_preference == default_pref:
        delete_query = """
                DELETE FROM server_notification_settings
                 WHERE user_id = $1 AND server_id = $2;
            """
        result = await DataBase.execute(delete_query, user_id, server_id)
        return result

    # If user is setting a custom preference, insert or update the record
    query = """
        INSERT INTO server_notification_settings (user_id, server_id, notification_preference)
             VALUES ($1, $2, $3)
        ON CONFLICT (user_id, server_id)
      DO UPDATE SET notification_preference = $3, updated_at = NOW()
        """
    return await DataBase.execute(query, user_id, server_id, notification_preference)


async def insert_batch_notifications(updates):
    placeholders = []
    params = []
    idx = 1
    for update in updates:
        # Build a placeholder string like "($1, $2, $3, $4, $5, NOW())"
        placeholders.append("(" + ", ".join([f"${i}" for i in range(idx, idx + 5)]) + ", NOW())")
        params.extend(
            [
                update.user_id,
                update.server_id,
                update.channel_id,
                update.unread_count,
                update.mention_count,
            ]
        )
        idx += 5

    query = f"""
        INSERT INTO user_notification_counters
                    (user_id, server_id, channel_id, unread_count, mention_count, updated_at)
             VALUES {', '.join(placeholders)}
        ON CONFLICT (user_id, server_id, channel_id)
      DO UPDATE SET
                    unread_count = user_notification_counters.unread_count + EXCLUDED.unread_count,
                    mention_count = user_notification_counters.mention_count + EXCLUDED.mention_count,
                    updated_at = NOW();
    """
    # Unpack the params list so that each value is passed as a separate argument.
    await DataBase.execute(query, *params)


async def get_batch_notification(user_id):
    query = """SELECT * FROM user_notification_counters WHERE user_id = $1 """
    return await DataBase.fetch(query, user_id)


async def clear_channel_notification(server_id, channel_id, user_id):
    query = """
    DELETE FROM user_notification_counters
          WHERE user_id = $1 AND server_id = $2 AND channel_id = $3
    """
    return await DataBase.execute(query, user_id, server_id, channel_id)
