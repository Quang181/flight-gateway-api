from fastapi import Request

from app.application.use_cases.create_booking import CreateBooking
from app.infrastructure.config.settings import get_settings
from app.application.use_cases.get_health_status import GetHealthStatus
from app.application.use_cases.get_booking import GetBooking
from app.application.use_cases.get_offer_detail import GetOfferDetail
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


def get_offer_detail_use_case(request: Request) -> GetOfferDetail:
    repository = request.app.state.flight_repository
    return GetOfferDetail(repository=repository)


def get_create_booking_use_case(request: Request) -> CreateBooking:
    repository = request.app.state.flight_repository
    return CreateBooking(repository=repository)


def get_booking_use_case(request: Request) -> GetBooking:
    settings = get_settings()
    repository = request.app.state.flight_repository
    return GetBooking(
        repository=repository,
        cache_ttl_seconds=settings.booking_cache_ttl_seconds,
    )
