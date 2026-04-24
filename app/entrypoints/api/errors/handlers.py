from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi import Request
from starlette.responses import JSONResponse

from app.entrypoints.api.errors.exceptions import AppHTTPException, LegacyApiException
from app.entrypoints.api.errors.responses import error_response


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc, LegacyApiException):
        return error_response(
            status_code=exc.status_code,
            message_key=exc.message,
            code=exc.error_code,
            accept_language=request.headers.get("lang"),
        )

    message_key = None
    code = None
    if isinstance(exc, AppHTTPException):
        message_key = exc.message_key
        code = exc.code

    return error_response(
        status_code=exc.status_code,
        message_key=message_key,
        code=code,
        accept_language=request.headers.get("lang"),
    )


async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        status_code=422,
        accept_language=request.headers.get("lang"),
    )


async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        status_code=500,
        accept_language=request.headers.get("lang"),
    )
