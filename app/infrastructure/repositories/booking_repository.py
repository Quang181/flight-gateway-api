from typing import Any
from sqlalchemy import func, select

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

    async def list_booking_records(
        self,
        *,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> dict[str, Any]:
        async with self._postgres._session_factory() as session:
            sort_column = self._resolve_sort_column(sort_by)
            order_by_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()

            total_items = await session.scalar(select(func.count()).select_from(BookingModel)) or 0
            offset = (page - 1) * page_size
            result = await session.execute(
                select(BookingModel)
                .order_by(order_by_clause)
                .offset(offset)
                .limit(page_size)
            )
            bookings = result.scalars().all()

            total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
            return {
                "items": [self._serialize_booking(booking) for booking in bookings],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages,
                },
            }

    @staticmethod
    def _resolve_sort_column(sort_by: str):
        if sort_by == "booking_reference":
            return BookingModel.booking_reference
        return BookingModel.created_at

    @staticmethod
    def _serialize_booking(booking: BookingModel) -> dict[str, Any]:
        return {
            "booking_reference": booking.booking_reference,
            "trip_type": booking.trip_type,
            "outbound_offer_id": booking.outbound_offer_id,
            "inbound_offer_id": booking.inbound_offer_id,
            "outbound_booking_ref": booking.outbound_booking_ref,
            "inbound_booking_ref": booking.inbound_booking_ref,
            "status": booking.status,
            "created_at": booking.created_at.isoformat().replace("+00:00", "Z") if booking.created_at else None,
            "updated_at": booking.updated_at.isoformat().replace("+00:00", "Z") if booking.updated_at else None,
        }
