from abc import ABC, abstractmethod
from typing import Any


class BookingRepository(ABC):
    @abstractmethod
    async def create_booking_record(self, payload: dict[str, Any]) -> None:
        """Persist a booking record."""

    @abstractmethod
    async def get_booking_record(self, booking_reference: str) -> dict[str, Any] | None:
        """Load a persisted booking record by booking reference."""

    @abstractmethod
    async def list_booking_records(
        self,
        *,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> dict[str, Any]:
        """Load persisted booking records with pagination and sorting."""
