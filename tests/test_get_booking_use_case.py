import pytest

from app.application.use_cases.get_booking import GetBooking
from app.entrypoints.api.errors.exceptions import AppNotFoundError


class FakeFlightRepository:
    def __init__(self, booking_results: dict[str, dict] | None = None) -> None:
        self.booking_results = booking_results or {}
        self.cache: dict[str, dict] = {}
        self.get_booking_calls: list[str] = []

    async def get_airports(self) -> dict:
        raise NotImplementedError

    async def get_airport_detail(self, code: str) -> dict:
        raise NotImplementedError

    async def search_flights(self, criteria: dict) -> dict:
        raise NotImplementedError

    async def get_offer_detail(self, offer_id: str) -> dict:
        raise NotImplementedError

    async def create_booking(self, payload: dict) -> dict:
        raise NotImplementedError

    async def get_booking(self, reference: str) -> dict:
        self.get_booking_calls.append(reference)
        return self.booking_results[reference]

    async def get(self, key: str) -> dict | None:
        return self.cache.get(key)

    async def set(self, key: str, value: dict, ttl_seconds: int) -> None:
        self.cache[key] = value

    async def set_offer_metadata(self, offer_id: str, value: dict, ttl_seconds: int) -> None:
        raise NotImplementedError

    async def get_offer_metadata(self, offer_id: str) -> dict | None:
        raise NotImplementedError


class FakeBookingRepository:
    def __init__(self, records: dict[str, dict] | None = None) -> None:
        self.records = records or {}

    async def create_booking_record(self, payload: dict) -> None:
        raise NotImplementedError

    async def get_booking_record(self, booking_reference: str) -> dict | None:
        return self.records.get(booking_reference)


@pytest.mark.anyio
async def test_get_booking_rejects_when_reference_missing_from_db() -> None:
    use_case = GetBooking(
        repository=FakeFlightRepository(),
        booking_repository=FakeBookingRepository(),
        cache_ttl_seconds=300,
    )

    with pytest.raises(AppNotFoundError) as exc_info:
        await use_case.execute("BOOK-REF-1")

    assert exc_info.value.code == "BOOKING_REFERENCE_NOT_FOUND"
    assert exc_info.value.message_key == "booking_reference_not_found"


@pytest.mark.anyio
async def test_get_booking_one_way_loads_outbound_only_from_legacy() -> None:
    repository = FakeFlightRepository(
        booking_results={
            "LEGACY-OUT-1": {
                "reservation": {
                    "booking_ref": "LEGACY-OUT-1",
                    "pnr": "PNR-OUT",
                    "status": "confirmed",
                    "StatusCode": "CONFIRMED",
                    "created_at": "2026-05-01T08:00:00Z",
                    "contact": {"email": "test@gmail.com", "phone": "082187382131"},
                    "passengers": [],
                    "ticketing": {"status": "confirmed", "ticket_numbers": []},
                }
            }
        }
    )
    booking_repository = FakeBookingRepository(
        records={
            "BOOK-REF-1": {
                "booking_reference": "BOOK-REF-1",
                "trip_type": "one_way",
                "outbound_booking_ref": "LEGACY-OUT-1",
                "inbound_booking_ref": None,
            }
        }
    )
    use_case = GetBooking(repository=repository, booking_repository=booking_repository, cache_ttl_seconds=300)

    result = await use_case.execute("BOOK-REF-1")

    assert repository.get_booking_calls == ["LEGACY-OUT-1"]
    assert result["booking_reference"] == "BOOK-REF-1"
    assert result["trip_type"] == "one_way"
    assert result["outbound"]["booking_reference"] == "LEGACY-OUT-1"
    assert result["outbound"]["summary"]["pnr"] == "PNR-OUT"
    assert result["inbound"] is None


@pytest.mark.anyio
async def test_get_booking_round_trip_loads_both_outbound_and_inbound_from_legacy() -> None:
    repository = FakeFlightRepository(
        booking_results={
            "LEGACY-OUT-1": {
                "reservation": {
                    "booking_ref": "LEGACY-OUT-1",
                    "pnr": "PNR-OUT",
                    "status": "confirmed",
                    "StatusCode": "CONFIRMED",
                    "created_at": "2026-05-01T08:00:00Z",
                    "contact": {"email": "test@gmail.com", "phone": "082187382131"},
                    "passengers": [],
                    "ticketing": {"status": "confirmed", "ticket_numbers": ["T1"]},
                }
            },
            "LEGACY-IN-1": {
                "reservation": {
                    "booking_ref": "LEGACY-IN-1",
                    "pnr": "PNR-IN",
                    "status": "confirmed",
                    "StatusCode": "CONFIRMED",
                    "created_at": "2026-05-02T08:00:00Z",
                    "contact": {"email": "test@gmail.com", "phone": "082187382131"},
                    "passengers": [],
                    "ticketing": {"status": "confirmed", "ticket_numbers": ["T2"]},
                }
            },
        }
    )
    booking_repository = FakeBookingRepository(
        records={
            "BOOK-REF-1": {
                "booking_reference": "BOOK-REF-1",
                "trip_type": "round_trip",
                "outbound_booking_ref": "LEGACY-OUT-1",
                "inbound_booking_ref": "LEGACY-IN-1",
            }
        }
    )
    use_case = GetBooking(repository=repository, booking_repository=booking_repository, cache_ttl_seconds=300)

    result = await use_case.execute("BOOK-REF-1")

    assert repository.get_booking_calls == ["LEGACY-OUT-1", "LEGACY-IN-1"]
    assert result["booking_reference"] == "BOOK-REF-1"
    assert result["trip_type"] == "round_trip"
    assert result["outbound"]["booking_reference"] == "LEGACY-OUT-1"
    assert result["inbound"]["booking_reference"] == "LEGACY-IN-1"
    assert result["inbound"]["summary"]["ticketing"]["ticket_numbers"] == ["T2"]


@pytest.mark.anyio
async def test_get_booking_uses_cache_before_db_and_legacy() -> None:
    repository = FakeFlightRepository()
    booking_repository = FakeBookingRepository(
        records={
            "BOOK-REF-1": {
                "booking_reference": "BOOK-REF-1",
                "trip_type": "one_way",
                "outbound_booking_ref": "LEGACY-OUT-1",
                "inbound_booking_ref": None,
            }
        }
    )
    use_case = GetBooking(repository=repository, booking_repository=booking_repository, cache_ttl_seconds=300)

    cached_value = {
        "booking_reference": "BOOK-REF-1",
        "trip_type": "one_way",
        "outbound": {"booking_reference": "LEGACY-OUT-1", "summary": {"pnr": "PNR-OUT"}},
        "inbound": None,
    }
    repository.cache[use_case._build_cache_key("BOOK-REF-1")] = cached_value

    result = await use_case.execute("BOOK-REF-1")

    assert result == cached_value
    assert repository.get_booking_calls == []
