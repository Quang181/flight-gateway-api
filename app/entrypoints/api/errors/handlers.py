from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi import Request
from starlette.responses import JSONResponse

from app.entrypoints.api.errors.exceptions import AppHTTPException
from app.entrypoints.api.errors.responses import error_response


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else None
    if isinstance(exc, AppHTTPException):
        message = exc.message

    return error_response(
        status_code=exc.status_code,
        message=message,
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
