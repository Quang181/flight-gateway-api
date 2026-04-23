import json
import logging
from typing import Any

from app.infrastructure.cache.redis import RedisManager

logger = logging.getLogger(__name__)


class FlightRedisCache:
    def __init__(self, redis: RedisManager) -> None:
        self._redis = redis

    async def get(self, key: str) -> dict[str, Any] | None:
        try:
            value = await self._redis._client.get(key)
        except Exception as exc:
            logger.warning("Redis cache get failed for key %s: %s", key, exc)
            return None
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        try:
            await self._redis._client.set(key, json.dumps(value), ex=ttl_seconds)
        except Exception as exc:
            logger.warning("Redis cache set failed for key %s: %s", key, exc)
