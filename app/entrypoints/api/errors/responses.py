from starlette.responses import JSONResponse

from app.entrypoints.api.errors.codes import ERROR_MESSAGE_KEYS, resolve_error_code
from app.entrypoints.api.errors.translations import translate


def error_response(
    status_code: int,
    message_key: str | None = None,
    code: str | None = None,
    accept_language: str | None = None,
) -> JSONResponse:
    resolved_message_key = message_key or ERROR_MESSAGE_KEYS.get(status_code, "unknown_error")
    payload = {
        "status_code": status_code,
        "message": translate(resolved_message_key, accept_language),
        "code": code or resolve_error_code(resolved_message_key, status_code),
    }
    return JSONResponse(status_code=status_code, content=payload)
