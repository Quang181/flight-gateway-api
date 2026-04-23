from pydantic import BaseModel, Field


class BookingPassengerResponse(BaseModel):
    pax_id: str | None = None
    type: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    title: str | None = None
    dob: str | None = None
    nationality: str | None = None
    passport_no: str | None = None


class BookingContactResponse(BaseModel):
    email: str | None = None
    phone: str | None = None


class BookingTicketingResponse(BaseModel):
    status: str | None = None
    time_limit: str | None = None
    ticket_numbers: list[str] = Field(default_factory=list)


class BookingSummaryResponse(BaseModel):
    pnr: str | None = None
    status: str | None = None
    status_code: str | None = None
    created_at: str | None = None
    contact: BookingContactResponse
    passengers: list[BookingPassengerResponse] = Field(default_factory=list)
    ticketing: BookingTicketingResponse


class BookingDetailResponse(BaseModel):
    booking_reference: str | None = None
    summary: BookingSummaryResponse
