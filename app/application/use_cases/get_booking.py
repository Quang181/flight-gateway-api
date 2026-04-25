import hashlib

from app.application.common.constant import BOOKING_CACHE_KEY_PREFIX
from app.application.common.legacy_normalization import normalize_booking
from app.application.common.upstream_errors import map_external_api_error
from app.domain.ports.booking_repository import BookingRepository
from app.domain.ports.flight_repository import FlightRepository
from app.entrypoints.api.errors.exceptions import AppNotFoundError


class GetBooking:
    def __init__(
        self,
        repository: FlightRepository,
        booking_repository: BookingRepository,
        cache_ttl_seconds: int,
    ) -> None:
        self._repository = repository
        self._booking_repository = booking_repository
        self._cache_ttl_seconds = cache_ttl_seconds

    async def execute(self, reference: str) -> dict:
        cache_key = self._build_cache_key(reference)
        cached = await self._repository.get(cache_key)
        if cached is not None:
            return cached

        booking_record = await self._booking_repository.get_booking_record(reference)
        if not isinstance(booking_record, dict):
            raise AppNotFoundError(
                message_key="booking_reference_not_found",
                code="BOOKING_REFERENCE_NOT_FOUND",
            )

        outbound = await self._load_legacy_booking(booking_record["outbound_booking_ref"])
        inbound = None
        if booking_record.get("trip_type") == "round_trip":
            inbound_reference = booking_record.get("inbound_booking_ref")
            if isinstance(inbound_reference, str) and inbound_reference.strip():
                inbound = await self._load_legacy_booking(inbound_reference)

        payload = {
            "booking_reference": reference,
            "trip_type": booking_record.get("trip_type"),
            "outbound": outbound,
            "inbound": inbound,
        }
        await self._repository.set(cache_key, payload, self._cache_ttl_seconds)
        return payload

    async def _load_legacy_booking(self, reference: str) -> dict:
        try:
            result = await self._repository.get_booking(reference)
        except Exception as exc:
            raise map_external_api_error(exc) from exc
        return normalize_booking(result)

    @staticmethod
    def _build_cache_key(reference: str) -> str:
        digest = hashlib.sha256(reference.encode("utf-8")).hexdigest()
        return f"{BOOKING_CACHE_KEY_PREFIX}:{digest}"
