ERROR_MESSAGE_KEYS: dict[int, str] = {
    200: "authorized",
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    429: "too_many_requests",
    422: "validation_error",
    502: "bad_gateway",
    503: "service_unavailable",
    504: "gateway_timeout",
    500: "internal_server_error",
}


ERROR_CODES: dict[str, str] = {
    # Common status-based codes
    "authorized": "AUTHORIZED",
    "bad_request": "BAD_REQUEST",
    "unauthorized": "UNAUTHORIZED",
    "forbidden": "FORBIDDEN",
    "not_found": "NOT_FOUND",
    "too_many_requests": "TOO_MANY_REQUESTS",
    "validation_error": "VALIDATION_ERROR",
    "bad_gateway": "BAD_GATEWAY",
    "service_unavailable": "SERVICE_UNAVAILABLE",
    "gateway_timeout": "GATEWAY_TIMEOUT",
    "internal_server_error": "INTERNAL_SERVER_ERROR",
    "unknown_error": "UNKNOWN_ERROR",

    # Booking errors
    "booking_create_rate_limited": "BOOKING_CREATE_RATE_LIMITED",
    "booking_create_validation_failed": "BOOKING_CREATE_VALIDATION_FAILED",
    "offer_id_required": "OFFER_ID_REQUIRED",
    "offer_id_not_found": "OFFER_ID_NOT_FOUND",
    "contact_email_required": "CONTACT_EMAIL_REQUIRED",
    "contact_phone_required": "CONTACT_PHONE_REQUIRED",
    "passengers_required": "PASSENGERS_REQUIRED",

    # Flight errors
    "flight_origin_destination_must_differ": "FLIGHT_ORIGIN_DESTINATION_MUST_DIFFER",
    "flight_origin_invalid_airport": "FLIGHT_ORIGIN_INVALID_AIRPORT",
    "flight_destination_invalid_airport": "FLIGHT_DESTINATION_INVALID_AIRPORT",

    # Upstream errors
    "upstream_timeout": "UPSTREAM_TIMEOUT",
    "upstream_rate_limited": "UPSTREAM_RATE_LIMITED",
    "upstream_unavailable": "UPSTREAM_UNAVAILABLE",
    "upstream_not_found": "UPSTREAM_NOT_FOUND",
    "upstream_bad_request": "UPSTREAM_BAD_REQUEST",
    "upstream_bad_payload": "UPSTREAM_BAD_PAYLOAD",
    "upstream_error": "UPSTREAM_ERROR",
}


def resolve_error_code(message_key: str | None, status_code: int) -> str:
    resolved_key = message_key or ERROR_MESSAGE_KEYS.get(status_code, "unknown_error")
    return ERROR_CODES.get(resolved_key, resolved_key.upper())
