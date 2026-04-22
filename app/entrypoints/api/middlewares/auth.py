from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match

from app.entrypoints.api.errors.responses import error_response
from app.infrastructure.config.settings import get_settings


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        endpoint = self._resolve_endpoint(request)
        if endpoint is None or not getattr(endpoint, "_require_token", False):
            return await call_next(request)

        settings = get_settings()
        token = request.headers.get(settings.auth_header_name)
        if token != settings.auth_token:
            return error_response(
                status_code=401,
                accept_language=request.headers.get("lang"),
            )

        return await call_next(request)

    @staticmethod
    def _resolve_endpoint(request: Request) -> Any | None:
        for route in request.app.router.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return getattr(route, "endpoint", None)
        return None
