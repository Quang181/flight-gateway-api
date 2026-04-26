from app.bootstrap import create_app


def test_create_booking_openapi_uses_detail_response_example() -> None:
    app = create_app()

    schema = app.openapi()

    post_booking_schema = schema["paths"]["/flights/bookings"]["post"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    assert post_booking_schema["$ref"] == "#/components/schemas/BookingDetailResponse"

    booking_detail_schema = schema["components"]["schemas"]["BookingDetailResponse"]
    example = booking_detail_schema["example"]

    assert example["trip_type"] == "round_trip"
    assert example["outbound"]["booking_reference"] == "BOOK-OUT"
    assert example["inbound"]["booking_reference"] == "BOOK-IN"


def test_create_booking_openapi_uses_request_body_example() -> None:
    app = create_app()

    schema = app.openapi()

    request_body_schema = schema["paths"]["/flights/bookings"]["post"]["requestBody"]["content"]["application/json"][
        "schema"
    ]
    assert request_body_schema["$ref"] == "#/components/schemas/BookingCreateRequest"

    booking_create_request_schema = schema["components"]["schemas"]["BookingCreateRequest"]
    example = booking_create_request_schema["example"]

    assert example["trip_type"] == "round_trip"
    assert example["offer_id_outbound"] == "offer-out-1"
    assert example["offer_id_inbound"] == "offer-in-1"
    assert example["contact"]["email"] == "test@gmail.com"
    assert len(example["passengers"]) == 1


def test_list_bookings_openapi_uses_paginated_response_example() -> None:
    app = create_app()

    schema = app.openapi()

    get_bookings_response_schema = schema["paths"]["/flights/bookings"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert get_bookings_response_schema["$ref"] == "#/components/schemas/BookingListResponse"

    booking_list_schema = schema["components"]["schemas"]["BookingListResponse"]
    example = booking_list_schema["example"]

    assert example["items"][0]["booking_reference"] == "BOOK-OUT"
    assert example["items"][0]["trip_type"] == "round_trip"
    assert example["pagination"]["page"] == 1
    assert example["pagination"]["page_size"] == 10
