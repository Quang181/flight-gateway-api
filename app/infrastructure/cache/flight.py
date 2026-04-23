import json
from typing import Any

from app.infrastructure.cache.redis import RedisManager


class FlightRedisCache:
    def __init__(self, redis: RedisManager) -> None:
        self._redis = redis

    async def get(self, key: str) -> dict[str, Any] | None:
        value = await self._redis._client.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        await self._redis._client.set(key, json.dumps(value), ex=ttl_seconds)
