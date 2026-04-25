import pytest

from app.entrypoints.api.errors.exceptions import AppTooManyRequestsError
from app.entrypoints.api.errors.translations import translate
from app.infrastructure.cache.booking_rate_limit import BookingCreateRateLimiter


class FakeRedisClient:
    def __init__(self, initial: dict[str, int] | None = None) -> None:
        self.values = dict(initial or {})
        self.expirations: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        value = self.values.get(key)
        return None if value is None else str(value)

    async def incr(self, key: str) -> int:
        value = self.values.get(key, 0) + 1
        self.values[key] = value
        return value

    async def expire(self, key: str, seconds: int) -> bool:
        self.expirations[key] = seconds
        return True


class FakeRedisManager:
    def __init__(self, initial: dict[str, int] | None = None) -> None:
        self._client = FakeRedisClient(initial)

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def incr(self, key: str) -> int:
        return await self._client.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        return await self._client.expire(key, seconds)


@pytest.mark.anyio
async def test_booking_create_rate_limiter_records_success_with_one_hour_ttl() -> None:
    redis = FakeRedisManager()
    limiter = BookingCreateRateLimiter(redis=redis)

    for _ in range(5):
        await limiter.record_success("203.0.113.10")

    assert redis._client.values["booking:create:ip:203.0.113.10"] == 5
    assert redis._client.expirations["booking:create:ip:203.0.113.10"] == 3600


@pytest.mark.anyio
async def test_booking_create_rate_limiter_blocks_after_five_successes() -> None:
    redis = FakeRedisManager({"booking:create:ip:203.0.113.11": 5})
    limiter = BookingCreateRateLimiter(redis=redis)

    with pytest.raises(AppTooManyRequestsError) as exc_info:
        await limiter.ensure_allowed("203.0.113.11")

    assert exc_info.value.status_code == 429
    assert exc_info.value.message_key == "booking_create_rate_limited"


@pytest.mark.anyio
async def test_booking_create_rate_limiter_ignores_failed_booking_until_success_is_recorded() -> None:
    redis = FakeRedisManager()
    limiter = BookingCreateRateLimiter(redis=redis)

    await limiter.ensure_allowed("203.0.113.12")

    assert redis._client.values == {}


def test_booking_create_rate_limit_message_supports_vietnamese_and_english() -> None:
    assert translate("booking_create_rate_limited", "vi") == "Ban da dat booking qua 5 lan. Vui long thu lai sau 1 gio."
    assert translate("booking_create_rate_limited", "en") == "You have created more than 5 bookings. Please try again after 1 hour."
