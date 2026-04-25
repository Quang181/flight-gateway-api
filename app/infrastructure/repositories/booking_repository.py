from typing import Any
from sqlalchemy import select

from app.domain.ports.booking_repository import BookingRepository
from app.infrastructure.db.models import BookingModel
from app.infrastructure.db.postgres import PostgresManager


class SqlAlchemyBookingRepository(BookingRepository):
    def __init__(self, postgres: PostgresManager) -> None:
        self._postgres = postgres

    async def create_booking_record(self, payload: dict[str, Any]) -> None:
        async with self._postgres._session_factory() as session:
            session.add(BookingModel(**payload))
            await session.commit()

    async def get_booking_record(self, booking_reference: str) -> dict[str, Any] | None:
        async with self._postgres._session_factory() as session:
            result = await session.execute(
                select(BookingModel).where(BookingModel.booking_reference == booking_reference)
            )
            booking = result.scalar_one_or_none()
            if booking is None:
                return None

            return {
                "booking_reference": booking.booking_reference,
                "trip_type": booking.trip_type,
                "outbound_offer_id": booking.outbound_offer_id,
                "inbound_offer_id": booking.inbound_offer_id,
                "outbound_booking_ref": booking.outbound_booking_ref,
                "inbound_booking_ref": booking.inbound_booking_ref,
                "status": booking.status,
            }
