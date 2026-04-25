import pytest

from app.application.use_cases.list_flights import ListFlights


class StubFlightRepository:
    def __init__(self, search_result: dict) -> None:
        self._search_result = search_result
        self._cache: dict[str, dict] = {}

    async def search_flights(self, criteria: dict) -> dict:
        return self._search_result

    async def get_airports(self) -> dict:
        return {
            "airports": [
                {"code": "SGN", "IATA": "SGN"},
                {"code": "KUL", "IATA": "KUL"},
            ]
        }

    async def get_airport_detail(self, code: str) -> dict:
        details = {
            "SGN": {"code": "SGN", "city": "Ho Chi Minh City", "name": "Tan Son Nhat International Airport"},
            "KUL": {"code": "KUL", "city": "Kuala Lumpur", "name": "Kuala Lumpur International Airport"},
        }
        return details[code.strip().upper()]

    async def get_offer_detail(self, offer_id: str) -> dict:
        raise NotImplementedError

    async def create_booking(self, payload: dict) -> dict:
        raise NotImplementedError

    async def get_booking(self, reference: str) -> dict:
        raise NotImplementedError

    async def get(self, key: str) -> dict | None:
        return self._cache.get(key)

    async def set(self, key: str, value: dict, ttl_seconds: int) -> None:
        self._cache[key] = value


@pytest.mark.anyio
async def test_list_flights_maps_airline_label_from_loaded_catalog() -> None:
    repository = StubFlightRepository(
        {
            "data": {
                "flight_results": {
                    "outbound": {
                        "results": [
                            {
                                "offer_id": "offer-1",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "SGN"},
                                                        "scheduled_time": "2026-05-01T08:00:00Z",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "KUL"},
                                                        "scheduled_time": "2026-05-01T10:00:00Z",
                                                    },
                                                    "carrier": {"marketing": "MH"},
                                                    "duration_minutes": 120,
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "stops": 0,
                                "total_journey_time": 120,
                                "pricing": {"currency": "USD", "totalAmountDecimal": 120.5},
                            }
                        ]
                    },
                    "inbound": {"results": []},
                }
            }
        }
    )
    use_case = ListFlights(
        repository=repository,
        cache_ttl_seconds=300,
        airline_labels={"MH": "Malaysia Airlines"},
    )

    result = await use_case.execute({"origin": "SGN", "destination": "KUL", "page": 1, "page_size": 10})

    assert result["direction"] == "outbound"
    assert result["items"][0]["offer_id"] == "offer-1"
    assert result["items"][0]["airline"] == {"code": "MH", "name": "Malaysia Airlines"}
