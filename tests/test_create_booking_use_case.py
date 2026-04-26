import pytest

from app.application.use_cases.create_booking import CreateBooking
from app.entrypoints.api.errors.exceptions import AppNotFoundError


class FakeFlightRepository:
    def __init__(
        self,
        offer_metadata: dict[str, dict] | None = None,
        booking_results: list[dict] | None = None,
    ) -> None:
        self.offer_metadata = offer_metadata or {}
        self.booking_results = booking_results or []
        self.create_booking_payloads: list[dict] = []

    async def get_airports(self) -> dict:
        raise NotImplementedError

    async def search_flights(self, criteria: dict) -> dict:
        raise NotImplementedError

    async def get_offer_detail(self, offer_id: str) -> dict:
        raise NotImplementedError

    async def create_booking(self, payload: dict) -> dict:
        self.create_booking_payloads.append(payload)
        return self.booking_results[len(self.create_booking_payloads) - 1]

    async def get_booking(self, reference: str) -> dict:
        raise NotImplementedError

    async def get(self, key: str) -> dict | None:
        raise NotImplementedError

    async def set(self, key: str, value: dict, ttl_seconds: int) -> None:
        raise NotImplementedError

    async def set_offer_metadata(self, offer_id: str, value: dict, ttl_seconds: int) -> None:
        self.offer_metadata[offer_id] = value

    async def get_offer_metadata(self, offer_id: str) -> dict | None:
        return self.offer_metadata.get(offer_id)


class FakeBookingRepository:
    def __init__(self) -> None:
        self.created: list[dict] = []

    async def create_booking_record(self, payload: dict) -> None:
        self.created.append(payload)


def _build_payload(**overrides: object) -> dict:
    payload = {
        "trip_type": "one_way",
        "offer_id_outbound": "offer-out-1",
        "offer_id_inbound": None,
        "passengers": [{"first_name": "Jane"}],
        "contact": {
            "email": "test@gmail.com",
            "phone": "082187382131",
        },
    }
    payload.update(overrides)
    return payload


@pytest.mark.anyio
async def test_create_booking_one_way_returns_detail_booking_shape() -> None:
    repository = FakeFlightRepository(
        offer_metadata={
            "offer-out-1": {
                "direction": "outbound",
                "origin": "HAN",
                "destination": "SGN",
                "departure_at": "2026-05-01T01:15:00Z",
            }
        },
        booking_results=[
            {
                "data": {
                    "booking_ref": "BOOK-OUT",
                    "pnr": "PNR-OUT",
                    "status": "confirmed",
                    "StatusCode": "CONFIRMED",
                    "created_at": "2026-05-01T08:00:00Z",
                    "contact": {"email": "test@gmail.com", "phone": "082187382131"},
                    "passengers": [
                        {
                            "pax_id": "PAX1",
                            "type": "ADT",
                            "first_name": "John",
                            "last_name": "Doe",
                            "name": "Doe/John Mr",
                            "title": "Mr",
                            "dob": "1995-05-20",
                            "nationality": "VN",
                            "passport_no": "B1234567",
                        }
                    ],
                    "ticketing": {"status": "confirmed", "ticket_numbers": []},
                }
            }
        ],
    )
    booking_repository = FakeBookingRepository()
    use_case = CreateBooking(repository=repository, booking_repository=booking_repository)

    result = await use_case.execute(_build_payload())

    assert result == {
        "booking_reference": "BOOK-OUT",
        "trip_type": "one_way",
        "passengers": [
            {
                "pax_id": "PAX1",
                "type": "ADT",
                "first_name": "John",
                "last_name": "Doe",
                "name": "Doe/John Mr",
                "title": "Mr",
                "dob": "1995-05-20",
                "nationality": "VN",
                "passport_no": "B1234567",
            }
        ],
        "outbound": {
            "booking_reference": "BOOK-OUT",
            "summary": {
                "pnr": "PNR-OUT",
                "status": "confirmed",
                "status_code": "CONFIRMED",
                "created_at": "2026-05-01T08:00:00Z",
                "contact": {"email": "test@gmail.com", "phone": "082187382131"},
                "ticketing": {
                    "status": "confirmed",
                    "time_limit": None,
                    "ticket_numbers": [],
                },
            },
        },
        "inbound": None,
    }


@pytest.mark.anyio
async def test_create_booking_rejects_outbound_offer_missing_from_outbound_index() -> None:
    repository = FakeFlightRepository(
        offer_metadata={
            "offer-in-1": {
                "direction": "inbound",
                "origin": "SGN",
                "destination": "HAN",
                "departure_at": "2026-05-10T09:20:00Z",
            }
        }
    )
    booking_repository = FakeBookingRepository()
    use_case = CreateBooking(repository=repository, booking_repository=booking_repository)

    with pytest.raises(AppNotFoundError) as exc_info:
        await use_case.execute(_build_payload())

    assert exc_info.value.code == "OFFER_ID_OUTBOUND_NOT_FOUND"
    assert repository.create_booking_payloads == []


@pytest.mark.anyio
async def test_create_booking_rejects_outbound_offer_with_wrong_direction() -> None:
    repository = FakeFlightRepository(
        offer_metadata={
            "offer-out-1": {
                "direction": "inbound",
                "origin": "HAN",
                "destination": "SGN",
                "departure_at": "2026-05-01T01:15:00Z",
            }
        }
    )
    booking_repository = FakeBookingRepository()
    use_case = CreateBooking(repository=repository, booking_repository=booking_repository)

    with pytest.raises(AppNotFoundError) as exc_info:
        await use_case.execute(_build_payload())

    assert exc_info.value.code == "OFFER_ID_OUTBOUND_INVALID_DIRECTION"
    assert exc_info.value.message_key == "offer_id_outbound_invalid_direction"
    assert repository.create_booking_payloads == []
    assert booking_repository.created == []


@pytest.mark.anyio
async def test_create_booking_rejects_inbound_offer_missing_from_inbound_index_before_legacy_call() -> None:
    repository = FakeFlightRepository(
        offer_metadata={
            "offer-out-1": {
                "direction": "outbound",
                "origin": "HAN",
                "destination": "SGN",
                "departure_at": "2026-05-01T01:15:00Z",
            }
        }
    )
    booking_repository = FakeBookingRepository()
    use_case = CreateBooking(repository=repository, booking_repository=booking_repository)

    with pytest.raises(AppNotFoundError) as exc_info:
        await use_case.execute(
            _build_payload(
                trip_type="round_trip",
                offer_id_inbound="offer-in-1",
            )
        )

    assert exc_info.value.code == "OFFER_ID_INBOUND_NOT_FOUND"
    assert exc_info.value.message_key == "offer_id_inbound_not_found"
    assert repository.create_booking_payloads == []
    assert booking_repository.created == []


@pytest.mark.anyio
async def test_create_booking_rejects_inbound_offer_with_wrong_direction() -> None:
    repository = FakeFlightRepository(
        offer_metadata={
            "offer-out-1": {
                "direction": "outbound",
                "origin": "HAN",
                "destination": "SGN",
                "departure_at": "2026-05-01T01:15:00Z",
            },
            "offer-in-1": {
                "direction": "outbound",
                "origin": "SGN",
                "destination": "HAN",
                "departure_at": "2026-05-10T09:20:00Z",
            },
        }
    )
    booking_repository = FakeBookingRepository()
    use_case = CreateBooking(repository=repository, booking_repository=booking_repository)

    with pytest.raises(AppNotFoundError) as exc_info:
        await use_case.execute(
            _build_payload(
                trip_type="round_trip",
                offer_id_inbound="offer-in-1",
            )
        )

    assert exc_info.value.code == "OFFER_ID_INBOUND_INVALID_DIRECTION"
    assert exc_info.value.message_key == "offer_id_inbound_invalid_direction"
    assert repository.create_booking_payloads == []
    assert booking_repository.created == []


@pytest.mark.anyio
async def test_create_booking_rejects_inbound_offer_with_non_reversed_route() -> None:
    repository = FakeFlightRepository(
        offer_metadata={
            "offer-out-1": {
                "direction": "outbound",
                "origin": "HAN",
                "destination": "SGN",
                "departure_at": "2026-05-01T01:15:00Z",
            },
            "offer-in-1": {
                "direction": "inbound",
                "origin": "KUL",
                "destination": "HAN",
                "departure_at": "2026-05-10T09:20:00Z",
            },
        }
    )
    booking_repository = FakeBookingRepository()
    use_case = CreateBooking(repository=repository, booking_repository=booking_repository)

    with pytest.raises(AppNotFoundError) as exc_info:
        await use_case.execute(
            _build_payload(
                trip_type="round_trip",
                offer_id_inbound="offer-in-1",
            )
        )

    assert exc_info.value.code == "OFFER_ID_INBOUND_INVALID_ROUTE"
    assert exc_info.value.message_key == "offer_id_inbound_invalid_route"
    assert repository.create_booking_payloads == []
    assert booking_repository.created == []


@pytest.mark.anyio
async def test_create_booking_rejects_round_trip_when_outbound_departs_after_inbound() -> None:
    repository = FakeFlightRepository(
        offer_metadata={
            "offer-out-1": {
                "direction": "outbound",
                "origin": "HAN",
                "destination": "SGN",
                "departure_at": "2026-05-11T09:20:00Z",
            },
            "offer-in-1": {
                "direction": "inbound",
                "origin": "SGN",
                "destination": "HAN",
                "departure_at": "2026-05-10T09:20:00Z",
            },
        }
    )
    booking_repository = FakeBookingRepository()
    use_case = CreateBooking(repository=repository, booking_repository=booking_repository)

    with pytest.raises(AppNotFoundError) as exc_info:
        await use_case.execute(
            _build_payload(
                trip_type="round_trip",
                offer_id_inbound="offer-in-1",
            )
        )

    assert exc_info.value.code == "OFFER_DEPARTURE_SEQUENCE_INVALID"
    assert exc_info.value.message_key == "offer_departure_sequence_invalid"
    assert repository.create_booking_payloads == []
    assert booking_repository.created == []


@pytest.mark.anyio
async def test_create_booking_round_trip_calls_legacy_twice_and_persists_record() -> None:
    repository = FakeFlightRepository(
        offer_metadata={
            "offer-out-1": {
                "direction": "outbound",
                "origin": "HAN",
                "destination": "SGN",
                "departure_at": "2026-05-01T01:15:00Z",
            },
            "offer-in-1": {
                "direction": "inbound",
                "origin": "SGN",
                "destination": "HAN",
                "departure_at": "2026-05-10T09:20:00Z",
            },
        },
        booking_results=[
            {
                "data": {
                    "booking_ref": "BOOK-OUT",
                    "pnr": "PNR-OUT",
                    "status": "confirmed",
                    "StatusCode": "CONFIRMED",
                    "created_at": "2026-05-01T08:00:00Z",
                    "contact": {"email": "test@gmail.com", "phone": "082187382131"},
                    "passengers": [
                        {
                            "pax_id": "PAX1",
                            "type": "ADT",
                            "first_name": "John",
                            "last_name": "Doe",
                            "name": "Doe/John Mr",
                            "title": "Mr",
                            "dob": "1995-05-20",
                            "nationality": "VN",
                            "passport_no": "B1234567",
                        }
                    ],
                    "ticketing": {"status": "confirmed", "ticket_numbers": []},
                }
            },
            {
                "data": {
                    "booking_ref": "BOOK-IN",
                    "pnr": "PNR-IN",
                    "status": "confirmed",
                    "StatusCode": "CONFIRMED",
                    "created_at": "2026-05-01T08:00:00Z",
                    "contact": {"email": "test@gmail.com", "phone": "082187382131"},
                    "passengers": [
                        {
                            "pax_id": "PAX1",
                            "type": "ADT",
                            "first_name": "John",
                            "last_name": "Doe",
                            "name": "Doe/John Mr",
                            "title": "Mr",
                            "dob": "1995-05-20",
                            "nationality": "VN",
                            "passport_no": "B1234567",
                        }
                    ],
                    "ticketing": {"status": "confirmed", "ticket_numbers": []},
                }
            },
        ],
    )
    booking_repository = FakeBookingRepository()
    use_case = CreateBooking(repository=repository, booking_repository=booking_repository)

    result = await use_case.execute(
        _build_payload(
            trip_type="round_trip",
            offer_id_inbound="offer-in-1",
        )
    )

    assert [payload["offer_id"] for payload in repository.create_booking_payloads] == ["offer-out-1", "offer-in-1"]
    assert repository.create_booking_payloads[0]["contact_email"] == "test@gmail.com"
    assert repository.create_booking_payloads[0]["contact_phone"] == "082187382131"
    assert "contact" not in repository.create_booking_payloads[0]
    assert repository.create_booking_payloads[1]["contact_email"] == "test@gmail.com"
    assert repository.create_booking_payloads[1]["contact_phone"] == "082187382131"
    assert "contact" not in repository.create_booking_payloads[1]
    assert booking_repository.created[0]["trip_type"] == "round_trip"
    assert booking_repository.created[0]["outbound_offer_id"] == "offer-out-1"
    assert booking_repository.created[0]["inbound_offer_id"] == "offer-in-1"
    assert booking_repository.created[0]["outbound_booking_ref"] == "BOOK-OUT"
    assert booking_repository.created[0]["inbound_booking_ref"] == "BOOK-IN"
    assert booking_repository.created[0]["status"] == "confirmed"
    assert result["booking_reference"] == "BOOK-OUT"
    assert result["trip_type"] == "round_trip"
    assert result["passengers"] == [
        {
            "pax_id": "PAX1",
            "type": "ADT",
            "first_name": "John",
            "last_name": "Doe",
            "name": "Doe/John Mr",
            "title": "Mr",
            "dob": "1995-05-20",
            "nationality": "VN",
            "passport_no": "B1234567",
        }
    ]
    assert result["outbound"]["booking_reference"] == "BOOK-OUT"
    assert result["outbound"]["summary"]["pnr"] == "PNR-OUT"
    assert "passengers" not in result["outbound"]["summary"]
    assert result["inbound"]["booking_reference"] == "BOOK-IN"
    assert result["inbound"]["summary"]["pnr"] == "PNR-IN"
    assert "passengers" not in result["inbound"]["summary"]
