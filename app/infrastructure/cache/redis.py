from redis.asyncio import Redis


class RedisManager:
    def __init__(self, redis_url: str) -> None:
        self._client = Redis.from_url(redis_url, decode_responses=True)

    async def connect(self) -> None:
        await self._client.ping()

    async def disconnect(self) -> None:
        await self._client.aclose()

    async def ping(self) -> str:
        await self._client.ping()
        return "ok"
