import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BookingModel(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("trip_type IN ('one_way', 'round_trip')", name="ck_bookings_trip_type"),
        CheckConstraint("status IN ('confirmed', 'partial_failed', 'failed')", name="ck_bookings_status"),
        CheckConstraint(
            "(trip_type = 'one_way' AND inbound_offer_id IS NULL AND inbound_booking_ref IS NULL) "
            "OR (trip_type = 'round_trip' AND inbound_offer_id IS NOT NULL)",
            name="ck_bookings_inbound_fields",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    trip_type: Mapped[str] = mapped_column(String(16), nullable=False)

    outbound_offer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    inbound_offer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    outbound_booking_ref: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    inbound_booking_ref: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

