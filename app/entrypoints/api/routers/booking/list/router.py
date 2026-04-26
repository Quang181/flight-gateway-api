from fastapi import APIRouter, Depends

from app.application.use_cases.list_bookings import ListBookings
from app.entrypoints.api.dependencies import get_list_bookings_use_case
from app.entrypoints.api.routers.booking.list.schema import BookingListQuery, BookingListResponse

router = APIRouter(prefix="/bookings")


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    query: BookingListQuery = Depends(),
    use_case: ListBookings = Depends(get_list_bookings_use_case),
) -> BookingListResponse:
    return BookingListResponse(**await use_case.execute(query.model_dump(mode="json")))
