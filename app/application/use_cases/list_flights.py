import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import BackgroundTasks

from app.application.common.constant import FLIGHT_SEARCH_CACHE_KEY_PREFIX
from app.application.common.legacy_normalization import normalize_trip_offer_summary
from app.application.common.pagination import Pagination
from app.domain.ports.flight_repository import FlightRepository
from app.entrypoints.api.errors.exceptions import AppValidationError


AIRPORTS_CACHE_KEY = f"{FLIGHT_SEARCH_CACHE_KEY_PREFIX}:airports"
AIRPORTS_CACHE_TTL_SECONDS = 3600

logger = logging.getLogger(__name__)


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

    async def execute(
        self,
        criteria: dict[str, Any],
        background_tasks: BackgroundTasks | None = None,
    ) -> dict[str, Any]:
        normalized_criteria = self._normalize_criteria(criteria)
        await self._validate_airports(normalized_criteria)
        direction = normalized_criteria.pop("direction", "outbound")
        sort_by = normalized_criteria.pop("sort_by", None)
        sort_order = normalized_criteria.pop("sort_order", "asc")
        page = normalized_criteria.pop("page", 1)
        page_size = normalized_criteria.pop("page_size", 10)
        cache_key = self._build_cache_key(
            {
                **normalized_criteria,
                "direction": direction,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "page": page,
                "page_size": page_size,
            }
        )

        cached_result = await self._repository.get(cache_key)
        if cached_result is not None:
            return cached_result

        result = await self._repository.search_flights(normalized_criteria)
        prepared_result = self._prepare_result(result, sort_by, sort_order)
        requested_payload = self._build_paginated_payload(
            direction=direction,
            items=prepared_result[direction],
            page=page,
            page_size=page_size,
        )
        await self._repository.set(cache_key, requested_payload, self._cache_ttl_seconds)

        if background_tasks is not None:
            background_tasks.add_task(
                self._cache_remaining_pages,
                normalized_criteria,
                prepared_result,
                page,
                page_size,
                sort_by,
                sort_order,
                direction,
            )

        return requested_payload

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
            raise AppValidationError(
                message_key="flight_origin_destination_must_differ",
                code="FLIGHT_ORIGIN_DESTINATION_MUST_DIFFER",
            )

        valid_codes = await self._get_valid_airport_codes()
        if origin not in valid_codes:
            raise AppValidationError(
                message_key="flight_origin_invalid_airport",
                code="FLIGHT_ORIGIN_INVALID_AIRPORT",
            )
        if destination not in valid_codes:
            raise AppValidationError(
                message_key="flight_destination_invalid_airport",
                code="FLIGHT_DESTINATION_INVALID_AIRPORT",
            )

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

    async def _cache_remaining_pages(
        self,
        criteria: dict[str, Any],
        prepared_result: dict[str, list[dict[str, Any]]],
        requested_page: int,
        page_size: int,
        sort_by: str | None,
        sort_order: str,
        requested_direction: str,
    ) -> None:
        logger.info(
            "Starting background flight cache warmup: requested_direction=%s requested_page=%s page_size=%s sort_by=%s sort_order=%s",
            requested_direction,
            requested_page,
            page_size,
            sort_by,
            sort_order,
        )
        for direction, items in prepared_result.items():
            total_items = len(items)
            total_pages = self._pagination.paginate(items, 1, page_size)["pagination"]["total_pages"]
            logger.info(
                "Preparing background cache pages for direction=%s total_items=%s total_pages=%s",
                direction,
                total_items,
                total_pages,
            )
            for page in range(1, total_pages + 1):
                if direction == requested_direction and page == requested_page:
                    continue
                payload = self._build_paginated_payload(
                    direction=direction,
                    items=items,
                    page=page,
                    page_size=page_size,
                )
                cache_key = self._build_cache_key(
                    {
                        **criteria,
                        "direction": direction,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "page": page,
                        "page_size": page_size,
                    }
                )
                await self._repository.set(cache_key, payload, self._cache_ttl_seconds)
                logger.info(
                    "Cached flight search page in background: direction=%s page=%s/%s items=%s cache_key=%s",
                    direction,
                    page,
                    total_pages,
                    len(payload["items"]),
                    cache_key,
                )
                print(f"{direction} {page}/{total_pages} {len(payload['items'])} {cache_key}")

            if total_items == 0:
                cache_key = self._build_cache_key(
                    {
                        **criteria,
                        "direction": direction,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                        "page": 1,
                        "page_size": page_size,
                    }
                )
                payload = self._build_paginated_payload(
                    direction=direction,
                    items=items,
                    page=1,
                    page_size=page_size,
                )
                await self._repository.set(cache_key, payload, self._cache_ttl_seconds)
                logger.info(
                    "Cached empty flight search page in background: direction=%s page=1/1 cache_key=%s",
                    direction,
                    cache_key,
                )
        logger.info(
            "Completed background flight cache warmup: requested_direction=%s requested_page=%s",
            requested_direction,
            requested_page,
        )

    def _prepare_result(
        self,
        result: dict[str, Any] | list[Any],
        sort_by: str | None,
        sort_order: str,
    ) -> dict[str, list[dict[str, Any]]]:
        return {
            "outbound": self._prepare_direction_items(
                self._extract_direction_items(result, "outbound"),
                sort_by,
                sort_order,
            ),
            "inbound": self._prepare_direction_items(
                self._extract_direction_items(result, "inbound"),
                sort_by,
                sort_order,
            ),
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

    def _prepare_direction_items(
        self,
        items: list[Any],
        sort_by: str | None,
        sort_order: str,
    ) -> list[dict[str, Any]]:
        normalized_items = [
            normalize_trip_offer_summary(item, self._airline_labels) if isinstance(item, dict) else item
            for item in items
        ]
        return self._sort_items(normalized_items, sort_by, sort_order)

    def _build_paginated_payload(
        self,
        direction: str,
        items: list[dict[str, Any]],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        paginated = self._pagination.paginate(items, page, page_size)
        return {
            "direction": direction,
            "items": paginated["items"],
            "pagination": paginated["pagination"],
        }

    def _sort_items(
        self,
        items: list[dict[str, Any]],
        sort_by: str | None,
        sort_order: str,
    ) -> list[dict[str, Any]]:
        if sort_by is None:
            return items

        reverse = sort_order == "desc"
        available_items = [item for item in items if self._sort_value(item, sort_by) is not None]
        missing_items = [item for item in items if self._sort_value(item, sort_by) is None]
        sorted_items = sorted(
            available_items,
            key=lambda item: self._sort_value(item, sort_by),
            reverse=reverse,
        )
        return [*sorted_items, *missing_items]

    def _sort_value(self, item: dict[str, Any], sort_by: str) -> Any | None:
        if sort_by == "price":
            price = item.get("price")
            amount = price.get("amount") if isinstance(price, dict) else None
            return amount

        return self._parse_sort_datetime(item.get(sort_by))

    @staticmethod
    def _parse_sort_datetime(value: Any) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
