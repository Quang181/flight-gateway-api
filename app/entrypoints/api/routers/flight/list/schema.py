from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.application.common.constant import DATE_YYYY_MM_DD_REGEX
from app.entrypoints.api.errors.exceptions import AppValidationError


class FlightListQuery(BaseModel):
    origin: str
    destination: str
    departure_date: str = Field(..., pattern=DATE_YYYY_MM_DD_REGEX)
    return_date: str = Field(..., pattern=DATE_YYYY_MM_DD_REGEX)
    pax_count: int
    cabin: Literal["Y", "W", "J", "F"] = "Y"
    direction: Literal["outbound", "inbound"] = "outbound"
    sort_by: Literal["price", "departure_at", "arrival_at"] | None = None
    sort_order: Literal["asc", "desc"] = "asc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

    @field_validator("departure_date")
    @classmethod
    def validate_departure_date(cls, value: str) -> str:
        return _validate_iso_date(value, message_key="departure_date_invalid", code="DEPARTURE_DATE_INVALID")

    @field_validator("return_date")
    @classmethod
    def validate_return_date(cls, value: str) -> str:
        return _validate_iso_date(value, message_key="return_date_invalid", code="RETURN_DATE_INVALID")


class FlightPriceResponse(BaseModel):
    amount: float
    currency: str | None = None
    display: str


class FlightDurationResponse(BaseModel):
    duration_minutes: int
    display: str


class FlightAirlineResponse(BaseModel):
    code: str | None = None
    name: str


class FlightRouteResponse(BaseModel):
    origin: str | None = None
    destination: str | None = None
    departure_at: str | None = None
    arrival_at: str | None = None
    stops: int | None = None
    duration: FlightDurationResponse | None = None


class FlightBaggagePieceResponse(BaseModel):
    pieces: int | None = None
    weight_kg: int | None = None


class FlightBaggageResponse(BaseModel):
    checked: FlightBaggagePieceResponse | None = None
    cabin: FlightBaggagePieceResponse | None = None


class FlightListItemResponse(BaseModel):
    offer_id: str | None = None
    airline: FlightAirlineResponse
    price: FlightPriceResponse | None = None
    route: FlightRouteResponse
    refundable: bool | None = None
    seats_remaining: int | None = None
    baggage: FlightBaggageResponse | None = None


class FlightPaginationResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class FlightTripGroupResponse(BaseModel):
    items: list[FlightListItemResponse] = Field(default_factory=list)
    pagination: FlightPaginationResponse


class FlightListResponse(BaseModel):
    direction: Literal["outbound", "inbound"]
    items: list[FlightListItemResponse] = Field(default_factory=list)
    pagination: FlightPaginationResponse


def _validate_iso_date(value: str, *, message_key: str, code: str) -> str:
    normalized = value.strip()
    try:
        parsed = date.fromisoformat(normalized)
    except ValueError as exc:
        raise AppValidationError(message_key=message_key, code=code) from exc
    return parsed.isoformat()
