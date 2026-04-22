from starlette.responses import JSONResponse

from app.entrypoints.api.errors.translations import translate

ERROR_MESSAGE_KEYS: dict[int, str] = {
    200: "authorized",
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    422: "validation_error",
    500: "internal_server_error",
}


def get_default_error_message(status_code: int, accept_language: str | None = None) -> str:
    message_key = ERROR_MESSAGE_KEYS.get(status_code, "unknown_error")
    return translate(message_key, accept_language)


def error_response(
    status_code: int,
    message: str | None = None,
    accept_language: str | None = None,
) -> JSONResponse:
    payload = {
        "status_code": status_code,
        "message": message or get_default_error_message(status_code, accept_language),
    }
    return JSONResponse(status_code=status_code, content=payload)
