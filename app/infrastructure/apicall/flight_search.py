from typing import Any

from app.infrastructure.apicall.base import BaseApiClient


class MockTravelFlightApiClient(BaseApiClient):
    async def search_flights(self, criteria: dict[str, Any]) -> dict[str, Any]:
        response = await self._post("/api/v1/flightsearch", json=criteria)
        return self.parse_json(response)
