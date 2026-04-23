from fastapi import Request

from app.infrastructure.config.settings import get_settings
from app.application.use_cases.get_health_status import GetHealthStatus
from app.application.use_cases.list_flights import ListFlights


def get_health_use_case(request: Request) -> GetHealthStatus:
    repository = request.app.state.health_repository
    return GetHealthStatus(repository=repository)


def get_list_flights_use_case(request: Request) -> ListFlights:
    settings = get_settings()
    repository = request.app.state.flight_repository
    return ListFlights(
        repository=repository,
        cache_ttl_seconds=settings.flight_search_cache_ttl_seconds,
    )
