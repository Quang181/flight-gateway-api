from app.entrypoints.api.errors.responses import error_response
from app.entrypoints.api.errors.translations import translate


def test_booking_create_inbound_offer_not_found_message_supports_vietnamese_and_english() -> None:
    assert translate("offer_id_inbound_not_found", "vi") == "offer_id_inbound khong ton tai trong inbound offers"
    assert translate("offer_id_inbound_not_found", "en") == "offer_id_inbound does not exist in inbound offers"


def test_booking_create_inbound_offer_not_found_error_response_uses_requested_language() -> None:
    response = error_response(
        status_code=404,
        message_key="offer_id_inbound_not_found",
        code="OFFER_ID_INBOUND_NOT_FOUND",
        accept_language="vi",
    )

    assert response.status_code == 404
    assert response.body == (
        b'{"status_code":404,"message":"offer_id_inbound khong ton tai trong inbound offers",'
        b'"code":"OFFER_ID_INBOUND_NOT_FOUND"}'
    )
