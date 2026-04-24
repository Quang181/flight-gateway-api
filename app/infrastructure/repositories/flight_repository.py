from typing import Any

from app.domain.ports.flight_repository import FlightRepository
from app.infrastructure.apicall.flight_search import MockTravelFlightApiClient
from app.infrastructure.cache.flight import FlightRedisCache


class MockTravelFlightRepository(FlightRepository):
    def __init__(self, api_client: MockTravelFlightApiClient, cache: FlightRedisCache) -> None:
        self._api_client = api_client
        self._cache = cache

    async def get_airports(self) -> dict[str, Any]:
        return await self._api_client.get_airports()

    async def search_flights(self, criteria: dict[str, Any]) -> dict[str, Any]:
        return await self._api_client.search_flights(criteria)

    async def get_offer_detail(self, offer_id: str) -> dict[str, Any]:
        return await self._api_client.get_offer_detail(offer_id)

    async def create_booking(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._api_client.create_booking(payload)

    async def get_booking(self, reference: str) -> dict[str, Any]:
        return await self._api_client.get_booking(reference)

    async def get(self, key: str) -> dict[str, Any] | None:
        return await self._cache.get(key)

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        await self._cache.set(key, value, ttl_seconds)
