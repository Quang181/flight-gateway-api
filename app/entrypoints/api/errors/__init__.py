from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.entrypoints.api.errors.exceptions import (
    AppAuthorizedResponse,
    AppBadRequestError,
    AppForbiddenError,
    AppHTTPException,
    AppInternalServerError,
    LegacyApiException,
    AppNotFoundError,
    AppUnauthorizedError,
    AppValidationError,
)
from app.entrypoints.api.errors.handlers import (
    handle_http_exception,
    handle_unexpected_exception,
    handle_validation_exception,
)

__all__ = [
    "AppAuthorizedResponse",
    "AppBadRequestError",
    "AppForbiddenError",
    "AppHTTPException",
    "AppInternalServerError",
    "LegacyApiException",
    "AppNotFoundError",
    "AppUnauthorizedError",
    "AppValidationError",
    "register_exception_handlers",
]


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(Exception, handle_unexpected_exception)
