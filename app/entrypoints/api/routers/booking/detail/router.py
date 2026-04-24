from fastapi import APIRouter, Depends

from app.application.use_cases.get_booking import GetBooking
from app.entrypoints.api.dependencies import get_booking_use_case
from app.entrypoints.api.routers.booking.detail.schema import BookingDetailResponse

router = APIRouter(prefix="/bookings")


@router.get("/{reference}", response_model=BookingDetailResponse)
# @require_token
async def get_booking(
    reference: str,
    use_case: GetBooking = Depends(get_booking_use_case),
) -> BookingDetailResponse:
    booking_detail = await use_case.execute(reference)
    response = BookingDetailResponse(**booking_detail)
    return response
