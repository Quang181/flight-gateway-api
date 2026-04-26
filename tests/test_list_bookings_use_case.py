import pytest

from app.application.use_cases.list_bookings import ListBookings


class FakeBookingRepository:
    def __init__(self, result: dict | None = None) -> None:
        self.result = result or {
            "items": [],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total_items": 0,
                "total_pages": 0,
            },
        }
        self.calls: list[dict] = []

    async def create_booking_record(self, payload: dict) -> None:
        raise NotImplementedError

    async def get_booking_record(self, booking_reference: str) -> dict | None:
        raise NotImplementedError

    async def list_booking_records(
        self,
        *,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> dict:
        self.calls.append(
            {
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
                "sort_order": sort_order,
            }
        )
        return self.result


@pytest.mark.anyio
async def test_list_bookings_passes_sort_and_pagination_to_repository() -> None:
    repository = FakeBookingRepository(
        result={
            "items": [
                {
                    "booking_reference": "BOOK-002",
                    "trip_type": "round_trip",
                    "outbound_offer_id": "offer-out-2",
                    "inbound_offer_id": "offer-in-2",
                    "outbound_booking_ref": "LEGACY-OUT-2",
                    "inbound_booking_ref": "LEGACY-IN-2",
                    "status": "confirmed",
                    "created_at": "2026-04-26T10:00:00Z",
                    "updated_at": "2026-04-26T10:05:00Z",
                }
            ],
            "pagination": {
                "page": 2,
                "page_size": 1,
                "total_items": 3,
                "total_pages": 3,
            },
        }
    )
    use_case = ListBookings(booking_repository=repository)

    result = await use_case.execute(
        {
            "page": 2,
            "page_size": 1,
            "sort_by": "booking_reference",
            "sort_order": "asc",
        }
    )

    assert repository.calls == [
        {
            "page": 2,
            "page_size": 1,
            "sort_by": "booking_reference",
            "sort_order": "asc",
        }
    ]
    assert result["items"][0]["booking_reference"] == "BOOK-002"
    assert result["pagination"] == {
        "page": 2,
        "page_size": 1,
        "total_items": 3,
        "total_pages": 3,
    }


@pytest.mark.anyio
async def test_list_bookings_uses_default_sort_and_pagination() -> None:
    repository = FakeBookingRepository()
    use_case = ListBookings(booking_repository=repository)

    await use_case.execute({})

    assert repository.calls == [
        {
            "page": 1,
            "page_size": 10,
            "sort_by": "created_at",
            "sort_order": "desc",
        }
    ]
