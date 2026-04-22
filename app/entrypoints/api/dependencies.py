from fastapi import Request

from app.application.use_cases.get_health_status import GetHealthStatus


def get_health_use_case(request: Request) -> GetHealthStatus:
    repository = request.app.state.health_repository
    return GetHealthStatus(repository=repository)
