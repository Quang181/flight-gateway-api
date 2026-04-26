from pydantic import BaseModel, ConfigDict, Field


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
    ticketing: BookingTicketingResponse


class BookingTripDetailResponse(BaseModel):
    booking_reference: str | None = None
    summary: BookingSummaryResponse


class BookingDetailResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "booking_reference": "BOOK-OUT",
                "trip_type": "round_trip",
                "passengers": [
                    {
                        "pax_id": "PAX1",
                        "type": "ADT",
                        "first_name": "John",
                        "last_name": "Doe",
                        "name": "Doe/John Mr",
                        "title": "Mr",
                        "dob": "1995-05-20",
                        "nationality": "VN",
                        "passport_no": "B1234567",
                    }
                ],
                "outbound": {
                    "booking_reference": "BOOK-OUT",
                    "summary": {
                        "pnr": "PNR-OUT",
                        "status": "confirmed",
                        "status_code": "CONFIRMED",
                        "created_at": "2026-05-01T08:00:00Z",
                        "contact": {
                            "email": "test@gmail.com",
                            "phone": "082187382131",
                        },
                        "ticketing": {
                            "status": "confirmed",
                            "time_limit": None,
                            "ticket_numbers": [],
                        },
                    },
                },
                "inbound": {
                    "booking_reference": "BOOK-IN",
                    "summary": {
                        "pnr": "PNR-IN",
                        "status": "confirmed",
                        "status_code": "CONFIRMED",
                        "created_at": "2026-05-01T08:00:00Z",
                        "contact": {
                            "email": "test@gmail.com",
                            "phone": "082187382131",
                        },
                        "ticketing": {
                            "status": "confirmed",
                            "time_limit": None,
                            "ticket_numbers": [],
                        },
                    },
                },
            }
        }
    )
    booking_reference: str | None = None
    trip_type: str | None = None
    passengers: list[BookingPassengerResponse] = Field(default_factory=list)
    outbound: BookingTripDetailResponse
    inbound: BookingTripDetailResponse | None = None
