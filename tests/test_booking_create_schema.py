import pytest

from app.entrypoints.api.routers.booking.create.schema import BookingCreateRequest
from app.entrypoints.api.errors.exceptions import AppValidationError


def test_booking_create_request_keeps_nested_contact_payload() -> None:
    request = BookingCreateRequest.model_validate(
        {
            "trip_type": "one_way",
            "offer_id_outbound": "offer-out-1",
            "passengers": [
                {
                    "title": "test",
                    "first_name": "ssd",
                    "last_name": "qdqwd",
                    "dob": "2025-11-11",
                    "nationality": "China",
                    "passport_no": "9182312312",
                    "email": "passenger@gmail.com",
                    "phone": "0987777712",
                }
            ],
            "contact": {
                "email": "test@gmail.com",
                "phone": "082187382131",
            },
        }
    )

    assert request.contact.email == "test@gmail.com"
    assert request.contact.phone == "082187382131"
    assert request.trip_type == "one_way"
    assert request.offer_id_outbound == "offer-out-1"
    assert request.offer_id_inbound is None
    assert request.model_dump(mode="json") == {
        "trip_type": "one_way",
        "offer_id_outbound": "offer-out-1",
        "offer_id_inbound": None,
        "passengers": [
            {
                "title": "test",
                "first_name": "ssd",
                "last_name": "qdqwd",
                "dob": "2025-11-11",
                "nationality": "China",
                "passport_no": "9182312312",
                "email": "passenger@gmail.com",
                "phone": "0987777712",
            }
        ],
        "contact": {
            "email": "test@gmail.com",
            "phone": "082187382131",
        },
    }
    assert not hasattr(request, "to_legacy_payload")


def test_booking_create_request_rejects_invalid_contact_phone() -> None:
    with pytest.raises(AppValidationError) as exc_info:
        BookingCreateRequest.model_validate(
            {
                "trip_type": "one_way",
                "offer_id_outbound": "offer-out-1",
                "passengers": [
                    {
                        "title": "test",
                        "first_name": "ssd",
                        "last_name": "qdqwd",
                        "dob": "2025-11-11",
                        "nationality": "China",
                        "passport_no": "9182312312",
                        "email": "passenger@gmail.com",
                        "phone": "0987777712",
                    }
                ],
                "contact": {
                    "email": "test@gmail.com",
                    "phone": "abcdefgh",
                },
            }
        )
    assert exc_info.value.code == "CONTACT_PHONE_INVALID"


def test_booking_create_request_requires_inbound_offer_for_round_trip() -> None:
    with pytest.raises(AppValidationError) as exc_info:
        BookingCreateRequest.model_validate(
            {
                "trip_type": "round_trip",
                "offer_id_outbound": "offer-out-1",
                "passengers": [
                    {
                        "title": "test",
                        "first_name": "ssd",
                        "last_name": "qdqwd",
                        "dob": "2025-11-11",
                        "nationality": "China",
                        "passport_no": "9182312312",
                        "email": "passenger@gmail.com",
                        "phone": "0987777712",
                    }
                ],
                "contact": {
                    "email": "test@gmail.com",
                    "phone": "082187382131",
                },
            }
        )

    assert exc_info.value.code == "OFFER_ID_INBOUND_REQUIRED"
