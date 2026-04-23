from fastapi import APIRouter, Body, Depends
from pydantic import ValidationError

from app.application.use_cases.create_booking import CreateBooking
from app.entrypoints.api.dependencies import get_create_booking_use_case
from app.entrypoints.api.errors.exceptions import AppValidationError
from app.entrypoints.api.routers.booking.create.schema import BookingCreateRequest, BookingCreateResponse

router = APIRouter(prefix="/bookings")


@router.post("", response_model=BookingCreateResponse)
# @require_token
async def create_booking(
        payload: BookingCreateRequest = Body(...),
        use_case: CreateBooking = Depends(get_create_booking_use_case),
) -> BookingCreateResponse:
    try:
        request = BookingCreateRequest.model_validate(payload)
    except ValidationError as exc:
        raise AppValidationError(message_key="booking_create_validation_failed") from exc
    create_booking = await use_case.execute(request.model_dump(mode="json"))
    response_create_booking = BookingCreateResponse(**create_booking)

    return response_create_booking
