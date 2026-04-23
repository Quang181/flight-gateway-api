from typing import Any

from app.infrastructure.apicall.base import BaseApiClient


class MockTravelFlightApiClient(BaseApiClient):
    async def search_flights(self, criteria: dict[str, Any]) -> dict[str, Any]:
        response = await self._post("/api/v1/flightsearch", json=criteria)
        return self.parse_json(response)

    async def get_offer_detail(self, offer_id: str) -> dict[str, Any]:
        response = await self._get(f"/api/v2/offer/{offer_id}")
        return self.parse_json(response)

    async def create_booking(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._post("/booking/create", json=payload)
        return self.parse_json(response)

    async def get_booking(self, reference: str) -> dict[str, Any]:
        response = await self._get(f"/api/v1/reservations/{reference}")
        return self.parse_json(response)
