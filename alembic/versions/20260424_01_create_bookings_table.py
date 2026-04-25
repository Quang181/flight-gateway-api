"""create bookings table

Revision ID: 20260424_01
Revises:
Create Date: 2026-04-24 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260424_01"
down_revision: str | None = "20260423_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_reference", sa.String(length=64), nullable=False),
        sa.Column("trip_type", sa.String(length=16), nullable=False),
        sa.Column("outbound_offer_id", sa.String(length=128), nullable=False),
        sa.Column("inbound_offer_id", sa.String(length=128), nullable=True),
        sa.Column("outbound_booking_ref", sa.String(length=128), nullable=False),
        sa.Column("inbound_booking_ref", sa.String(length=128), nullable=True),
        sa.Column("outbound_pnr", sa.String(length=64), nullable=True),
        sa.Column("inbound_pnr", sa.String(length=64), nullable=True),
        sa.Column("outbound_status", sa.String(length=32), nullable=True),
        sa.Column("inbound_status", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("raw_request", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("outbound_response", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("inbound_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("trip_type IN ('one_way', 'round_trip')", name="ck_bookings_trip_type"),
        sa.CheckConstraint("status IN ('confirmed', 'partial_failed', 'failed')", name="ck_bookings_status"),
        sa.CheckConstraint(
            "(trip_type = 'one_way' AND inbound_offer_id IS NULL AND inbound_booking_ref IS NULL "
            "AND inbound_response IS NULL AND inbound_pnr IS NULL AND inbound_status IS NULL) "
            "OR (trip_type = 'round_trip' AND inbound_offer_id IS NOT NULL)",
            name="ck_bookings_inbound_fields",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_reference"),
        sa.UniqueConstraint("outbound_booking_ref"),
        sa.UniqueConstraint("inbound_booking_ref"),
    )


def downgrade() -> None:
    op.drop_table("bookings")
