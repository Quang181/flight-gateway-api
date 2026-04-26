from fastapi import Request

from app.application.use_cases.create_booking import CreateBooking
from app.infrastructure.config.settings import get_settings
from app.application.use_cases.get_booking import GetBooking
from app.application.use_cases.list_bookings import ListBookings
from app.application.use_cases.get_offer_detail import GetOfferDetail
from app.application.use_cases.list_flights import ListFlights
from app.infrastructure.cache.booking_rate_limit import BookingCreateRateLimiter
from app.infrastructure.repositories.booking_repository import SqlAlchemyBookingRepository

def get_list_flights_use_case(request: Request) -> ListFlights:
    settings = get_settings()
    repository = request.app.state.flight_repository
    airline_labels = request.app.state.airline_labels
    return ListFlights(
        repository=repository,
        cache_ttl_seconds=settings.flight_search_cache_ttl_seconds,
        airline_labels=airline_labels,
    )


def get_offer_detail_use_case(request: Request) -> GetOfferDetail:
    repository = request.app.state.flight_repository
    return GetOfferDetail(repository=repository)


def get_create_booking_use_case(request: Request) -> CreateBooking:
    repository = request.app.state.flight_repository
    booking_repository = SqlAlchemyBookingRepository(postgres=request.app.state.postgres)
    return CreateBooking(repository=repository, booking_repository=booking_repository)


def get_booking_create_rate_limiter(request: Request) -> BookingCreateRateLimiter:
    redis = request.app.state.redis
    return BookingCreateRateLimiter(redis=redis)


def get_booking_use_case(request: Request) -> GetBooking:
    settings = get_settings()
    repository = request.app.state.flight_repository
    booking_repository = SqlAlchemyBookingRepository(postgres=request.app.state.postgres)
    return GetBooking(
        repository=repository,
        booking_repository=booking_repository,
        cache_ttl_seconds=settings.booking_cache_ttl_seconds,
    )


def get_list_bookings_use_case(request: Request) -> ListBookings:
    booking_repository = SqlAlchemyBookingRepository(postgres=request.app.state.postgres)
    return ListBookings(booking_repository=booking_repository)
