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

    async def add_to_set(self, key: str, values: list[str], ttl_seconds: int) -> None:
        if not values:
            return
        try:
            await self._redis.sadd(key, *values)
            await self._redis.expire(key, ttl_seconds)
        except Exception as exc:
            logger.warning("Redis cache sadd failed for key %s: %s", key, exc)

    async def is_in_set(self, key: str, value: str) -> bool:
        try:
            return await self._redis.sismember(key, value)
        except Exception as exc:
            logger.warning("Redis cache sismember failed for key %s: %s", key, exc)
            return False

    async def set_offer_metadata(self, offer_id: str, value: dict[str, Any], ttl_seconds: int) -> None:
        await self.set(f"flight:offer:{offer_id}", value, ttl_seconds)

    async def get_offer_metadata(self, offer_id: str) -> dict[str, Any] | None:
        return await self.get(f"flight:offer:{offer_id}")
