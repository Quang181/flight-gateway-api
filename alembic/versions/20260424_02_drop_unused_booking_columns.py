"""drop unused booking columns

Revision ID: 20260424_02
Revises: 20260424_01
Create Date: 2026-04-24 00:00:01.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260424_02"
down_revision: str | None = "20260424_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_bookings_inbound_fields", "bookings", type_="check")
    op.drop_column("bookings", "inbound_response")
    op.drop_column("bookings", "outbound_response")
    op.drop_column("bookings", "raw_request")
    op.drop_column("bookings", "contact_phone")
    op.drop_column("bookings", "contact_email")
    op.drop_column("bookings", "inbound_status")
    op.drop_column("bookings", "outbound_status")
    op.drop_column("bookings", "inbound_pnr")
    op.drop_column("bookings", "outbound_pnr")
    op.create_check_constraint(
        "ck_bookings_inbound_fields",
        "bookings",
        "(trip_type = 'one_way' AND inbound_offer_id IS NULL AND inbound_booking_ref IS NULL) "
        "OR (trip_type = 'round_trip' AND inbound_offer_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_bookings_inbound_fields", "bookings", type_="check")
    op.add_column(
        "bookings",
        sa.Column("outbound_pnr", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("inbound_pnr", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("outbound_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("inbound_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("contact_email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("raw_request", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.add_column(
        "bookings",
        sa.Column("outbound_response", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.add_column(
        "bookings",
        sa.Column("inbound_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_check_constraint(
        "ck_bookings_inbound_fields",
        "bookings",
        "(trip_type = 'one_way' AND inbound_offer_id IS NULL AND inbound_booking_ref IS NULL "
        "AND inbound_response IS NULL AND inbound_pnr IS NULL AND inbound_status IS NULL) "
        "OR (trip_type = 'round_trip' AND inbound_offer_id IS NOT NULL)",
    )
