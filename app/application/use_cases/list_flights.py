import hashlib
import json
from typing import Any

from app.application.common.constant import FLIGHT_SEARCH_CACHE_KEY_PREFIX
from app.application.common.pagination import Pagination
from app.domain.ports.flight_repository import FlightRepository


class ListFlights:
    def __init__(
        self,
        repository: FlightRepository,
        cache_ttl_seconds: int,
    ) -> None:
        self._repository = repository
        self._cache_ttl_seconds = cache_ttl_seconds
        self._pagination = Pagination()

    async def execute(self, criteria: dict[str, Any]) -> dict[str, Any]:
        normalized_criteria = self._normalize_criteria(criteria)
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
        return {key: value for key, value in criteria.items() if value is not None}

    @staticmethod
    def _build_cache_key(criteria: dict[str, Any]) -> str:
        raw_key = json.dumps(criteria, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return f"{FLIGHT_SEARCH_CACHE_KEY_PREFIX}:{digest}"

    def _paginate_result(self, result: dict[str, Any] | list[Any], page: int, page_size: int) -> dict[str, Any]:
        items = self._extract_items(result)
        paginated = self._pagination.paginate(items, page, page_size)
        metadata = self._extract_metadata(result)
        return {
            **metadata,
            "items": paginated["items"],
            "pagination": paginated["pagination"],
        }

    @staticmethod
    def _extract_items(result: dict[str, Any] | list[Any]) -> list[Any]:
        if isinstance(result, list):
            return result

        for key in ("data", "items", "flights", "results"):
            value = result.get(key)
            if isinstance(value, list):
                return value

        for value in result.values():
            if isinstance(value, list):
                return value

        return []

    @staticmethod
    def _extract_metadata(result: dict[str, Any] | list[Any]) -> dict[str, Any]:
        if isinstance(result, list):
            return {}

        return {
            key: value
            for key, value in result.items()
            if not isinstance(value, list) and key not in {"data", "items", "flights", "results"}
        }
