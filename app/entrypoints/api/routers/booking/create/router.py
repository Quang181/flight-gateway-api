from fastapi import APIRouter, Body, Depends, Request

from app.application.use_cases.create_booking import CreateBooking
from app.entrypoints.api.dependencies import (
    get_booking_create_rate_limiter,
    get_create_booking_use_case,
)
from app.entrypoints.api.routers.booking.create.schema import BookingCreateRequest
from app.entrypoints.api.routers.booking.detail.schema import BookingDetailResponse
from app.infrastructure.cache.booking_rate_limit import BookingCreateRateLimiter

router = APIRouter(prefix="/bookings")


@router.post("", response_model=BookingDetailResponse)
# @require_token
async def create_booking(
        request: Request,
        payload: BookingCreateRequest = Body(...),
        use_case: CreateBooking = Depends(get_create_booking_use_case),
        rate_limiter: BookingCreateRateLimiter = Depends(get_booking_create_rate_limiter),
) -> BookingDetailResponse:
    client_ip = _get_client_ip(request)
    await rate_limiter.ensure_allowed(client_ip)
    create_booking = await use_case.execute(payload.model_dump(mode="json"))
    await rate_limiter.record_success(client_ip)
    response_create_booking = BookingDetailResponse(**create_booking)

    return response_create_booking


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"
