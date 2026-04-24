from typing import Literal

from pydantic import BaseModel, Field

from app.application.common.constant import DATE_YYYY_MM_DD_REGEX


class FlightListQuery(BaseModel):
    origin: str
    destination: str
    departure_date: str = Field(..., pattern=DATE_YYYY_MM_DD_REGEX)
    return_date: str = Field(..., pattern=DATE_YYYY_MM_DD_REGEX)
    pax_count: int
    cabin: Literal["Y", "W", "J", "F"] = "Y"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class FlightPriceResponse(BaseModel):
    amount: float
    currency: str | None = None
    display: str


class FlightDurationResponse(BaseModel):
    duration_minutes: int
    display: str


class FlightListItemResponse(BaseModel):
    price: FlightPriceResponse | None = None
    airline_name: str
    departure_at: str | None = None
    arrival_at: str | None = None
    stops: int | None = None
    flight_duration: FlightDurationResponse | None = None


class FlightPaginationResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class FlightTripGroupResponse(BaseModel):
    items: list[FlightListItemResponse] = Field(default_factory=list)
    pagination: FlightPaginationResponse


class FlightListResponse(BaseModel):
    outbound: FlightTripGroupResponse
    inbound: FlightTripGroupResponse
