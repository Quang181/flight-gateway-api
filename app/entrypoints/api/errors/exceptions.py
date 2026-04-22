from starlette.exceptions import HTTPException

from app.entrypoints.api.errors.responses import ERROR_MESSAGE_KEYS


class AppHTTPException(HTTPException):
    def __init__(self, status_code: int, message: str | None = None) -> None:
        self.message = message
        self.message_key = ERROR_MESSAGE_KEYS.get(status_code, "unknown_error")
        super().__init__(status_code=status_code, detail=message)


class AppAuthorizedResponse(AppHTTPException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(status_code=200, message=message)


class AppBadRequestError(AppHTTPException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(status_code=400, message=message)


class AppUnauthorizedError(AppHTTPException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(status_code=401, message=message)


class AppForbiddenError(AppHTTPException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(status_code=403, message=message)


class AppNotFoundError(AppHTTPException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(status_code=404, message=message)


class AppValidationError(AppHTTPException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(status_code=422, message=message)


class AppInternalServerError(AppHTTPException):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(status_code=500, message=message)
