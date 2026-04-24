import hashlib
import json
from typing import Any

from app.application.common.constant import FLIGHT_SEARCH_CACHE_KEY_PREFIX
from app.application.common.legacy_normalization import normalize_trip_offer_summary
from app.application.common.pagination import Pagination
from app.domain.ports.flight_repository import FlightRepository
from app.entrypoints.api.errors.exceptions import AppValidationError


AIRPORTS_CACHE_KEY = f"{FLIGHT_SEARCH_CACHE_KEY_PREFIX}:airports"
AIRPORTS_CACHE_TTL_SECONDS = 3600


class ListFlights:
    def __init__(
        self,
        repository: FlightRepository,
        cache_ttl_seconds: int,
        airline_labels: dict[str, str],
    ) -> None:
        self._repository = repository
        self._cache_ttl_seconds = cache_ttl_seconds
        self._airline_labels = airline_labels
        self._pagination = Pagination()

    async def execute(self, criteria: dict[str, Any]) -> dict[str, Any]:
        normalized_criteria = self._normalize_criteria(criteria)
        await self._validate_airports(normalized_criteria)
        page = normalized_criteria.pop("page", 1)
        page_size = normalized_criteria.pop("page_size", 10)
        cache_key = self._build_cache_key({**normalized_criteria, "page": page, "page_size": page_size})

        cached_result = await self._repository.get(cache_key)
        if cached_result is not None:
            return cached_result

        result = await self._repository.search_flights(normalized_criteria)
        paginated_result = self._paginate_result(result, page, page_size)
        await self._repository.set(cache_key, paginated_result, self._cache_ttl_seconds)
        return paginated_result

    @staticmethod
    def _normalize_criteria(criteria: dict[str, Any]) -> dict[str, Any]:
        normalized = {key: value for key, value in criteria.items() if value is not None}
        for airport_field in ("origin", "destination"):
            airport_code = normalized.get(airport_field)
            if isinstance(airport_code, str):
                normalized[airport_field] = airport_code.strip().upper()
        return normalized

    async def _validate_airports(self, criteria: dict[str, Any]) -> None:
        origin = criteria.get("origin")
        destination = criteria.get("destination")

        if not isinstance(origin, str) or not isinstance(destination, str):
            return

        if origin == destination:
            raise AppValidationError(message_key="flight_origin_destination_must_differ")

        valid_codes = await self._get_valid_airport_codes()
        if origin not in valid_codes:
            raise AppValidationError(message_key="flight_origin_invalid_airport")
        if destination not in valid_codes:
            raise AppValidationError(message_key="flight_destination_invalid_airport")

    async def _get_valid_airport_codes(self) -> set[str]:
        cached_catalog = await self._repository.get(AIRPORTS_CACHE_KEY)
        catalog = cached_catalog if cached_catalog is not None else await self._repository.get_airports()

        if cached_catalog is None:
            await self._repository.set(AIRPORTS_CACHE_KEY, catalog, AIRPORTS_CACHE_TTL_SECONDS)

        airports = catalog.get("airports", []) if isinstance(catalog, dict) else []
        valid_codes: set[str] = set()
        for airport in airports:
            if not isinstance(airport, dict):
                continue
            for field_name in ("code", "IATA"):
                airport_code = airport.get(field_name)
                if isinstance(airport_code, str) and airport_code.strip():
                    valid_codes.add(airport_code.strip().upper())
        return valid_codes

    @staticmethod
    def _build_cache_key(criteria: dict[str, Any]) -> str:
        raw_key = json.dumps(criteria, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return f"{FLIGHT_SEARCH_CACHE_KEY_PREFIX}:{digest}"

    def _paginate_result(self, result: dict[str, Any] | list[Any], page: int, page_size: int) -> dict[str, Any]:
        return {
            "outbound": self._paginate_direction(self._extract_direction_items(result, "outbound"), page, page_size),
            "inbound": self._paginate_direction(self._extract_direction_items(result, "inbound"), page, page_size),
        }

    @staticmethod
    def _extract_direction_items(result: dict[str, Any] | list[Any], direction: str) -> list[Any]:
        if not isinstance(result, dict):
            return []

        direction_payload = (
            result.get("data", {})
            .get("flight_results", {})
            .get(direction, {})
        )
        items = direction_payload.get("results")
        return items if isinstance(items, list) else []

    def _paginate_direction(self, items: list[Any], page: int, page_size: int) -> dict[str, Any]:
        normalized_items = [
            normalize_trip_offer_summary(item, self._airline_labels) if isinstance(item, dict) else item
            for item in items
        ]
        paginated = self._pagination.paginate(normalized_items, page, page_size)
        return {
            "items": paginated["items"],
            "pagination": paginated["pagination"],
        }
