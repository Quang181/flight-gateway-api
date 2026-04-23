from starlette.exceptions import HTTPException

from app.entrypoints.api.errors.responses import ERROR_MESSAGE_KEYS


class AppHTTPException(HTTPException):
    def __init__(self, status_code: int, message: str | None = None, message_key: str | None = None) -> None:
        self.message = message
        self.message_key = message_key or ERROR_MESSAGE_KEYS.get(status_code, "unknown_error")
        super().__init__(status_code=status_code, detail=message)


class AppAuthorizedResponse(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=200, message=message, message_key=message_key)


class AppBadRequestError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=400, message=message, message_key=message_key)


class AppUnauthorizedError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=401, message=message, message_key=message_key)


class AppForbiddenError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=403, message=message, message_key=message_key)


class AppNotFoundError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=404, message=message, message_key=message_key)


class AppTooManyRequestsError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=429, message=message, message_key=message_key)


class AppValidationError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=422, message=message, message_key=message_key)


class AppBadGatewayError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=502, message=message, message_key=message_key)


class AppServiceUnavailableError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=503, message=message, message_key=message_key)


class AppGatewayTimeoutError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=504, message=message, message_key=message_key)


class AppInternalServerError(AppHTTPException):
    def __init__(self, message: str | None = None, message_key: str | None = None) -> None:
        super().__init__(status_code=500, message=message, message_key=message_key)


class LegacyApiException(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.request_id = request_id
