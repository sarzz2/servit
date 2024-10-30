import logging

from redis.asyncio import Redis

log = logging.getLogger("fastapi")


class RedisClient:
    def __init__(self, host="localhost", port=6379, decode_responses=True):
        self.client = Redis(host=host, port=port, decode_responses=decode_responses)

    async def connect(self):
        try:
            await self.client.ping()
            log.info("Connected to Redis successfully.")
        except Exception as e:
            log.critical(f"Failed to connect to Redis: {e}")
            raise RuntimeError("Redis connection failed")

    async def close(self):
        await self.client.aclose()
