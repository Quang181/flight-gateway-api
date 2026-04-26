from typing import Any

from app.domain.ports.booking_repository import BookingRepository


class ListBookings:
    def __init__(self, booking_repository: BookingRepository) -> None:
        self._booking_repository = booking_repository

    async def execute(self, criteria: dict[str, Any]) -> dict[str, Any]:
        return await self._booking_repository.list_booking_records(
            page=criteria.get("page", 1),
            page_size=criteria.get("page_size", 10),
            sort_by=criteria.get("sort_by", "created_at"),
            sort_order=criteria.get("sort_order", "desc"),
        )
