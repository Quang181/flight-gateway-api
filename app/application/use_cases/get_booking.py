import hashlib

from app.application.common.constant import BOOKING_CACHE_KEY_PREFIX
from app.application.common.legacy_normalization import normalize_booking
from app.application.common.upstream_errors import map_external_api_error
from app.domain.ports.flight_repository import FlightRepository


class GetBooking:
    def __init__(self, repository: FlightRepository, cache_ttl_seconds: int) -> None:
        self._repository = repository
        self._cache_ttl_seconds = cache_ttl_seconds

    async def execute(self, reference: str) -> dict:
        cache_key = self._build_cache_key(reference)
        cached = await self._repository.get(cache_key)
        if cached is not None:
            return cached
        try:
            result = await self._repository.get_booking(reference)
        except Exception as exc:
            raise map_external_api_error(exc) from exc
        booking = normalize_booking(result)
        await self._repository.set(cache_key, booking, self._cache_ttl_seconds)
        return booking

    @staticmethod
    def _build_cache_key(reference: str) -> str:
        digest = hashlib.sha256(reference.encode("utf-8")).hexdigest()
        return f"{BOOKING_CACHE_KEY_PREFIX}:{digest}"
