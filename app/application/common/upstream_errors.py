from fastapi import HTTPException

from app.entrypoints.api.errors.exceptions import (
    AppBadGatewayError,
    AppBadRequestError,
    AppGatewayTimeoutError,
    AppInternalServerError,
    AppNotFoundError,
    AppServiceUnavailableError,
    AppTooManyRequestsError,
)
from app.infrastructure.apicall.base import (
    ExternalApiError,
    ExternalApiResponseError,
    ExternalApiTimeoutError,
)


def map_external_api_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ExternalApiTimeoutError):
        raise AppGatewayTimeoutError(message_key="upstream_timeout")

    if isinstance(exc, ExternalApiResponseError):
        if exc.status_code == 429:
            raise AppTooManyRequestsError(message_key="upstream_rate_limited")

        if exc.status_code == 503:
            raise AppServiceUnavailableError(message_key="upstream_unavailable")

        if exc.status_code == 404:
            raise AppNotFoundError(message_key="upstream_not_found")

        if exc.status_code == 400:
            raise AppBadRequestError(message_key="upstream_bad_request")

        if exc.status_code == 502 or exc.details.get("reason") == "invalid_json":
            raise AppBadGatewayError(message_key="upstream_bad_payload")

    if isinstance(exc, ExternalApiError):
        raise AppInternalServerError(message_key="upstream_error")

    raise AppInternalServerError(message_key="unknown_error")
