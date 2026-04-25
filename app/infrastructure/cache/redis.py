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

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def incr(self, key: str) -> int:
        return await self._client.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        return await self._client.expire(key, seconds)

    async def sadd(self, key: str, *values: str) -> int:
        return await self._client.sadd(key, *values)

    async def sismember(self, key: str, value: str) -> bool:
        return bool(await self._client.sismember(key, value))
