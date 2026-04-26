from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BookingListQuery(BaseModel):
    sort_by: Literal["created_at", "booking_reference"] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class BookingListItemResponse(BaseModel):
    booking_reference: str
    trip_type: str
    outbound_offer_id: str
    inbound_offer_id: str | None = None
    outbound_booking_ref: str
    inbound_booking_ref: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None


class BookingListPaginationResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class BookingListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "booking_reference": "BOOK-OUT",
                        "trip_type": "round_trip",
                        "outbound_offer_id": "offer-out-1",
                        "inbound_offer_id": "offer-in-1",
                        "outbound_booking_ref": "LEGACY-OUT-1",
                        "inbound_booking_ref": "LEGACY-IN-1",
                        "status": "confirmed",
                        "created_at": "2026-04-26T10:00:00Z",
                        "updated_at": "2026-04-26T10:05:00Z",
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total_items": 1,
                    "total_pages": 1,
                },
            }
        }
    )
    items: list[BookingListItemResponse] = Field(default_factory=list)
    pagination: BookingListPaginationResponse
