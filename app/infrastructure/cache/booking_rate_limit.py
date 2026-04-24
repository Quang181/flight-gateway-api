import logging

from app.entrypoints.api.errors.exceptions import AppTooManyRequestsError
from app.infrastructure.cache.redis import RedisManager


logger = logging.getLogger(__name__)


class BookingCreateRateLimiter:
    KEY_PREFIX = "booking:create:ip:"
    LIMIT = 5
    TTL_SECONDS = 3600

    def __init__(self, redis: RedisManager) -> None:
        self._redis = redis

    async def ensure_allowed(self, client_ip: str) -> None:
        attempts = await self._get_attempts(client_ip)
        if attempts >= self.LIMIT:
            raise AppTooManyRequestsError(
                message_key="booking_create_rate_limited",
                code="BOOKING_CREATE_RATE_LIMITED",
            )

    async def record_success(self, client_ip: str) -> None:
        key = self._build_key(client_ip)
        try:
            attempts = await self._redis.incr(key)
            if attempts == 1:
                await self._redis.expire(key, self.TTL_SECONDS)
        except Exception as exc:
            logger.warning("Booking create rate limit update failed for key %s: %s", key, exc)

    async def _get_attempts(self, client_ip: str) -> int:
        key = self._build_key(client_ip)
        try:
            value = await self._redis.get(key)
        except Exception as exc:
            logger.warning("Booking create rate limit lookup failed for key %s: %s", key, exc)
            return 0

        if value is None:
            return 0

        try:
            return int(value)
        except (TypeError, ValueError):
            logger.warning("Booking create rate limit value is invalid for key %s: %r", key, value)
            return 0

    @classmethod
    def _build_key(cls, client_ip: str) -> str:
        normalized_ip = client_ip.strip() or "unknown"
        return f"{cls.KEY_PREFIX}{normalized_ip}"
