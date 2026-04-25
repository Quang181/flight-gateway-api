import pytest
from fastapi import BackgroundTasks

from app.application.use_cases.list_flights import ListFlights
from app.entrypoints.api.errors.exceptions import AppValidationError


class StubFlightRepository:
    def __init__(self, search_result: dict) -> None:
        self._search_result = search_result
        self._cache: dict[str, dict] = {}
        self.airports_calls = 0
        self.airport_detail_calls: list[str] = []
        self.airports_payload = {
            "airports": [
                {"code": "HAN", "IATA": "HAN"},
                {"code": "SGN", "IATA": "SGN"},
                {"code": "KUL", "IATA": "KUL"},
            ]
        }
        self.last_search_criteria: dict | None = None
        self.offer_metadata: dict[str, dict] = {}
        self.offer_metadata_ttls: dict[str, int] = {}

    async def search_flights(self, criteria: dict) -> dict:
        self.last_search_criteria = criteria
        return self._search_result

    async def get_offer_detail(self, offer_id: str) -> dict:
        raise NotImplementedError

    async def create_booking(self, payload: dict) -> dict:
        raise NotImplementedError

    async def get_booking(self, reference: str) -> dict:
        raise NotImplementedError

    async def get_airports(self) -> dict:
        self.airports_calls += 1
        return self.airports_payload

    async def get_airport_detail(self, code: str) -> dict:
        normalized_code = code.strip().upper()
        self.airport_detail_calls.append(normalized_code)
        details = {
            "HAN": {"code": "HAN", "city": "Hanoi", "name": "Noi Bai International Airport"},
            "SGN": {"code": "SGN", "city": "Ho Chi Minh City", "name": "Tan Son Nhat International Airport"},
            "KUL": {"code": "KUL", "city": "Kuala Lumpur", "name": "Kuala Lumpur International Airport"},
            "SIN": {"code": "SIN", "city": "Singapore", "name": "Singapore Changi Airport"},
        }
        return details.get(normalized_code, {"code": normalized_code, "name": normalized_code})

    async def get(self, key: str) -> dict | None:
        return self._cache.get(key)

    async def set(self, key: str, value: dict, ttl_seconds: int) -> None:
        self._cache[key] = value

    async def set_offer_metadata(self, offer_id: str, value: dict, ttl_seconds: int) -> None:
        self.offer_metadata[offer_id] = value
        self.offer_metadata_ttls[offer_id] = ttl_seconds

    async def get_offer_metadata(self, offer_id: str) -> dict | None:
        return self.offer_metadata.get(offer_id)


@pytest.mark.anyio
async def test_list_flights_groups_outbound_and_inbound_with_normalized_fields() -> None:
    repository = StubFlightRepository(
        {
            "Status": "OK",
            "StatusCode": 200,
            "data": {
                "flight_results": {
                    "outbound": {
                        "results": [
                            {
                                "offer_id": "offer-1",
                                "offerId": "offer-1",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "HAN", "terminal": "2"},
                                                        "scheduled_time": "11-Nov-2026 06:15 AM",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "SGN", "terminal": "1"},
                                                        "scheduled_time": "2026-11-11T08:19:00+07:00",
                                                    },
                                                    "carrier": {
                                                        "marketing": "MH",
                                                        "number": "MH268",
                                                    },
                                                    "duration_minutes": 124,
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "stops": 0,
                                "total_journey_time": 124,
                                "pricing": {
                                    "currency": "MYR",
                                    "totalAmountDecimal": 163.89,
                                },
                                "seats_remaining": 3,
                                "refundable": False,
                                "baggage": {
                                    "checked": {"pieces": 1, "weight_kg": 20, "Weight": "20KG"},
                                    "cabin_baggage": {"pieces": 1, "weight_kg": 7},
                                },
                            },
                            {
                                "offer_id": "offer-2",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "HAN"},
                                                        "scheduled_time": "2026-11-11T08:30:00+07:00",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "SIN"},
                                                        "scheduled_time": "11/11/2026 11:27",
                                                    },
                                                    "carrier": {
                                                        "marketing": "AK",
                                                        "number": "AK940",
                                                    },
                                                    "duration_minutes": 177,
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "stops": 1,
                                "total_journey_time": 461,
                                "pricing": {
                                    "currency": "MYR",
                                    "totalAmountDecimal": 183.72,
                                },
                            },
                        ],
                        "result_count": 2,
                    },
                    "inbound": {
                        "results": [
                            {
                                "offer_id": "offer-3",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "SGN"},
                                                        "scheduled_time": "30/11/2026 12:00",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "HAN"},
                                                        "scheduled_time": 1796020920,
                                                    },
                                                    "carrier": {
                                                        "marketing": "MH",
                                                        "number": "MH835",
                                                    },
                                                    "duration_minutes": 102,
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "stops": 0,
                                "total_journey_time": 102,
                                "pricing": {
                                    "currency": "MYR",
                                    "totalAmountDecimal": 242.22,
                                },
                            }
                        ],
                        "result_count": 1,
                    },
                }
            },
        }
    )
    use_case = ListFlights(
        repository=repository,
        cache_ttl_seconds=300,
        airline_labels={"MH": "Malaysia Airlines", "AK": "AirAsia"},
    )

    result = await use_case.execute({"origin": "HAN", "destination": "SGN", "page": 1, "page_size": 1})

    assert set(result) == {"direction", "items", "pagination"}
    assert result["direction"] == "outbound"
    assert result["pagination"] == {
        "page": 1,
        "page_size": 1,
        "total_items": 2,
        "total_pages": 2,
    }
    assert result["items"] == [
        {
            "offer_id": "offer-1",
            "airline": {
                "code": "MH",
                "name": "Malaysia Airlines",
            },
            "price": {
                "amount": 163.89,
                "currency": "MYR",
                "display": "MYR 163.89",
            },
            "route": {
                "origin": "Hanoi",
                "destination": "Ho Chi Minh City",
                "departure_at": "2026-11-11T06:15:00Z",
                "arrival_at": "2026-11-11T01:19:00Z",
                "stops": 0,
                "duration": {
                    "duration_minutes": 124,
                    "display": "2h 04m",
                },
            },
            "refundable": False,
            "seats_remaining": 3,
            "baggage": {
                "checked": {
                    "pieces": 1,
                    "weight_kg": 20,
                },
                "cabin": {
                    "pieces": 1,
                    "weight_kg": 7,
                },
            },
        }
    ]


@pytest.mark.anyio
async def test_list_flights_rejects_same_origin_and_destination() -> None:
    repository = StubFlightRepository({"data": {"flight_results": {"outbound": {"results": []}, "inbound": {"results": []}}}})
    use_case = ListFlights(
        repository=repository,
        cache_ttl_seconds=300,
        airline_labels={},
    )

    with pytest.raises(AppValidationError) as exc_info:
        await use_case.execute({"origin": "han", "destination": "HAN", "page": 1, "page_size": 10})

    assert exc_info.value.message_key == "flight_origin_destination_must_differ"


@pytest.mark.anyio
async def test_list_flights_rejects_airport_code_not_found_in_catalog() -> None:
    repository = StubFlightRepository({"data": {"flight_results": {"outbound": {"results": []}, "inbound": {"results": []}}}})
    use_case = ListFlights(
        repository=repository,
        cache_ttl_seconds=300,
        airline_labels={},
    )

    with pytest.raises(AppValidationError) as exc_info:
        await use_case.execute({"origin": "XXX", "destination": "SGN", "page": 1, "page_size": 10})

    assert exc_info.value.message_key == "flight_origin_invalid_airport"


@pytest.mark.anyio
async def test_list_flights_uses_cached_airport_catalog_and_normalizes_search_criteria() -> None:
    repository = StubFlightRepository(
        {"data": {"flight_results": {"outbound": {"results": []}, "inbound": {"results": []}}}}
    )
    use_case = ListFlights(
        repository=repository,
        cache_ttl_seconds=300,
        airline_labels={},
    )

    await use_case.execute({"origin": "han", "destination": "sgn", "page": 1, "page_size": 10})
    await use_case.execute({"origin": "HAN", "destination": "SGN", "page": 1, "page_size": 10})

    assert repository.airports_calls == 1
    assert repository.last_search_criteria is not None
    assert repository.last_search_criteria["origin"] == "HAN"
    assert repository.last_search_criteria["destination"] == "SGN"


@pytest.mark.anyio
async def test_list_flights_caches_offer_metadata_per_offer_id() -> None:
    repository = StubFlightRepository(
        {
            "data": {
                "flight_results": {
                    "outbound": {
                        "results": [
                            {
                                "offer_id": "offer-out-1",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "HAN"},
                                                        "scheduled_time": "12/11/2026 18:15",
                                                        "dt": "12/11/2026 18:15",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "SGN"},
                                                        "scheduled_time": "12-Nov-2026 08:20 PM",
                                                    },
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "pricing": {"currency": "USD", "totalAmountDecimal": 120.50},
                            }
                        ]
                    },
                    "inbound": {
                        "results": [
                            {
                                "offer_id": "offer-in-1",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "SGN"},
                                                        "dt": "2026-11-20T07:35:00+07:00",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "HAN"},
                                                        "scheduled_time": "20-Nov-2026 09:40 AM",
                                                    },
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "pricing": {"currency": "USD", "totalAmountDecimal": 125.50},
                            }
                        ]
                    },
                }
            }
        }
    )
    use_case = ListFlights(
        repository=repository,
        cache_ttl_seconds=300,
        airline_labels={"VN": "Vietnam Airlines"},
    )
    background_tasks = BackgroundTasks()

    await use_case.execute(
        {
            "origin": "SGN",
            "destination": "HAN",
            "departure_date": "2026-05-01",
            "return_date": "2026-05-10",
            "pax_count": 1,
            "cabin": "Y",
            "direction": "outbound",
            "page": 1,
            "page_size": 10,
        },
        background_tasks=background_tasks,
    )

    for task in background_tasks.tasks:
        await task.func(*task.args, **task.kwargs)

    assert repository.offer_metadata["offer-out-1"] == {
        "direction": "outbound",
        "origin": "SGN",
        "destination": "HAN",
        "departure_at": "2026-11-12T18:15:00Z",
    }
    assert repository.offer_metadata["offer-in-1"] == {
        "direction": "inbound",
        "origin": "HAN",
        "destination": "SGN",
        "departure_at": "2026-11-20T00:35:00Z",
    }
    assert repository.offer_metadata_ttls["offer-out-1"] == 300
    assert repository.offer_metadata_ttls["offer-in-1"] == 300


@pytest.mark.anyio
async def test_list_flights_maps_priority_request_airports_to_full_names() -> None:
    repository = StubFlightRepository(
        {
            "data": {
                "flight_results": {
                    "outbound": {
                        "results": [
                            {
                                "offer_id": "offer-out-1",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "HAN"},
                                                        "scheduled_time": "12/11/2026 18:15",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "SGN"},
                                                        "scheduled_time": "12-Nov-2026 08:20 PM",
                                                    },
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "pricing": {"currency": "USD", "totalAmountDecimal": 120.50},
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
        airline_labels={},
    )

    result = await use_case.execute({"origin": "HAN", "destination": "SGN", "page": 1, "page_size": 10})

    assert result["items"][0]["route"]["origin"] == "Hanoi"
    assert result["items"][0]["route"]["destination"] == "Ho Chi Minh City"
    assert repository.airport_detail_calls == ["HAN", "SGN"]


@pytest.mark.anyio
async def test_list_flights_warms_remaining_airport_details_in_background() -> None:
    repository = StubFlightRepository(
        {
            "data": {
                "flight_results": {
                    "outbound": {
                        "results": [
                            {
                                "offer_id": "offer-out-1",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "HAN"},
                                                        "scheduled_time": "12/11/2026 18:15",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "SGN"},
                                                        "scheduled_time": "12-Nov-2026 08:20 PM",
                                                    },
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "pricing": {"currency": "USD", "totalAmountDecimal": 120.50},
                            },
                            {
                                "offer_id": "offer-out-2",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "HAN"},
                                                        "scheduled_time": "13/11/2026 09:15",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "KUL"},
                                                        "scheduled_time": "13-Nov-2026 01:20 PM",
                                                    },
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "pricing": {"currency": "USD", "totalAmountDecimal": 160.50},
                            },
                        ]
                    },
                    "inbound": {
                        "results": [
                            {
                                "offer_id": "offer-in-1",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "SGN"},
                                                        "scheduled_time": "15/11/2026 10:15",
                                                    },
                                                    "arrival_info": {
                                                        "airport": {"code": "SIN"},
                                                        "scheduled_time": "15-Nov-2026 01:20 PM",
                                                    },
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "pricing": {"currency": "USD", "totalAmountDecimal": 140.50},
                            }
                        ]
                    },
                }
            }
        }
    )
    use_case = ListFlights(
        repository=repository,
        cache_ttl_seconds=300,
        airline_labels={},
    )
    background_tasks = BackgroundTasks()

    await use_case.execute(
        {"origin": "HAN", "destination": "SGN", "page": 1, "page_size": 10},
        background_tasks=background_tasks,
    )

    assert repository.airport_detail_calls == ["HAN", "SGN"]

    for task in background_tasks.tasks:
        await task.func(*task.args, **task.kwargs)

    assert repository.airport_detail_calls == ["HAN", "SGN", "KUL", "SIN"]
    assert repository._cache["flight_search:airports:detail:KUL"] == {
        "code": "KUL",
        "city": "Kuala Lumpur",
        "name": "Kuala Lumpur International Airport",
    }
    assert repository._cache["flight_search:airports:detail:SIN"] == {
        "code": "SIN",
        "city": "Singapore",
        "name": "Singapore Changi Airport",
    }


@pytest.mark.anyio
async def test_list_flights_skips_offer_metadata_when_departure_time_missing() -> None:
    repository = StubFlightRepository(
        {
            "data": {
                "flight_results": {
                    "outbound": {
                        "results": [
                            {
                                "offer_id": "offer-out-1",
                                "segments": {
                                    "segment_list": [
                                        {
                                            "leg_data": [
                                                {
                                                    "departure_info": {
                                                        "airport": {"code": "SGN"},
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "pricing": {"currency": "USD", "totalAmountDecimal": 120.50},
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
        airline_labels={"VN": "Vietnam Airlines"},
    )
    background_tasks = BackgroundTasks()

    await use_case.execute(
        {
            "origin": "SGN",
            "destination": "HAN",
            "departure_date": "2026-05-01",
            "return_date": "2026-05-10",
            "pax_count": 1,
            "cabin": "Y",
            "direction": "outbound",
            "page": 1,
            "page_size": 10,
        },
        background_tasks=background_tasks,
    )

    for task in background_tasks.tasks:
        await task.func(*task.args, **task.kwargs)

    assert repository.offer_metadata == {}
