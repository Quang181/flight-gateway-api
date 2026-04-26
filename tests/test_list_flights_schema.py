import pytest

from app.entrypoints.api.errors.exceptions import AppValidationError
from app.entrypoints.api.routers.flight.list.schema import FlightListQuery, FlightListResponse


def test_flight_list_response_schema_accepts_normalized_trip_groups() -> None:
    payload = {
        "direction": "outbound",
        "items": [
            {
                "offer_id": "offer-1",
                "airline": {
                    "code": "MH",
                    "name": "Malaysia Airlines",
                },
                "price": {
                    "amount": 233.95,
                    "currency": "MYR",
                    "display": "MYR 233.95",
                },
                "route": {
                    "origin": "HAN",
                    "destination": "KUL",
                    "departure_at": "2025-11-12T14:55:00Z",
                    "arrival_at": "2025-11-12T09:42:00Z",
                    "stops": 0,
                    "duration": {
                        "duration_minutes": 107,
                        "display": "1h 47m",
                    },
                },
                "refundable": False,
                "seats_remaining": 3,
                "baggage": {
                    "checked": {"pieces": 1, "weight_kg": 20},
                    "cabin": {"pieces": 1, "weight_kg": 7},
                },
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 1,
            "total_items": 7,
            "total_pages": 7,
        },
    }

    response = FlightListResponse(**payload)

    assert response.direction == "outbound"
    assert response.items[0].airline.name == "Malaysia Airlines"
    assert response.pagination.total_items == 7


def test_flight_list_query_rejects_invalid_departure_date() -> None:
    with pytest.raises(AppValidationError) as exc_info:
        FlightListQuery.model_validate(
            {
                "origin": "HAN",
                "destination": "KUL",
                "departure_date": "2026-13-12",
                "return_date": "2026-12-20",
                "pax_count": 1,
            }
        )

    assert exc_info.value.code == "DEPARTURE_DATE_INVALID"
    assert exc_info.value.message_key == "departure_date_invalid"


def test_flight_list_query_rejects_invalid_return_date() -> None:
    with pytest.raises(AppValidationError) as exc_info:
        FlightListQuery.model_validate(
            {
                "origin": "HAN",
                "destination": "KUL",
                "departure_date": "2026-12-12",
                "return_date": "2026-02-30",
                "pax_count": 1,
            }
        )

    assert exc_info.value.code == "RETURN_DATE_INVALID"
    assert exc_info.value.message_key == "return_date_invalid"
