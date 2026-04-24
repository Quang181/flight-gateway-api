import re
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


EMAIL_REGEX = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
PHONE_REGEX = re.compile(r"^\d{8,20}$")
PASSPORT_REGEX = re.compile(r"^[A-Z0-9]{6,20}$", re.IGNORECASE)



class BookingPassenger(BaseModel):
    title: str = Field(..., min_length=1)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    dob: str = Field(..., min_length=1)
    nationality: str = Field(..., min_length=1)
    passport_no: str = Field(..., min_length=6, max_length=20)
    email: str = Field(..., min_length=3)
    phone: str = Field(..., min_length=8, max_length=20)

    @field_validator("passport_no")
    @classmethod
    def validate_passport_no(cls, value: str) -> str:
        normalized = value.strip()
        if not PASSPORT_REGEX.fullmatch(normalized):
            raise ValueError("passport_no must be 6-20 alphanumeric characters")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip()
        if not EMAIL_REGEX.fullmatch(normalized):
            raise ValueError("email is invalid")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not PHONE_REGEX.fullmatch(normalized):
            raise ValueError("phone must contain 8-20 digits")
        return normalized

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, value: str) -> str:
        normalized = value.strip()
        try:
            parsed = date.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("dob must be a valid date in YYYY-MM-DD format") from exc
        return parsed.isoformat()


class BookingContact(BaseModel):
    email: str = Field(..., min_length=3)
    phone: str = Field(..., min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip()
        if not EMAIL_REGEX.fullmatch(normalized):
            raise ValueError("email is invalid")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not PHONE_REGEX.fullmatch(normalized):
            raise ValueError("phone must contain 8-20 digits")
        return normalized


class BookingCreateRequest(BaseModel):
    offer_id: str = Field(..., min_length=1)
    passengers: list[BookingPassenger] = Field(..., min_length=1)
    contact: BookingContact

    @model_validator(mode="after")
    def validate_unique_passenger_contacts(self) -> "BookingCreateRequest":
        seen_emails: set[str] = set()
        seen_phones: set[str] = set()
        seen_passport_numbers: set[str] = set()

        for passenger in self.passengers:
            email = passenger.email.strip().lower()
            phone = passenger.phone.strip()
            passport_no = passenger.passport_no.strip().upper()

            if email in seen_emails:
                raise ValueError("each passenger email must be unique")
            if phone in seen_phones:
                raise ValueError("each passenger phone must be unique")
            if passport_no in seen_passport_numbers:
                raise ValueError("each passenger passport_no must be unique")

            seen_emails.add(email)
            seen_phones.add(phone)
            seen_passport_numbers.add(passport_no)

        return self

    def to_legacy_payload(self) -> dict[str, object]:
        payload = self.model_dump(mode="json")
        contact = payload.pop("contact", {})
        payload["contact_email"] = contact.get("email")
        payload["contact_phone"] = contact.get("phone")
        return payload


class BookingCreateContactResponse(BaseModel):
    email: str | None = None
    phone: str | None = None


class BookingCreatePassengerResponse(BaseModel):
    pax_id: str | None = None
    type: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    title: str | None = None
    dob: str | None = None
    nationality: str | None = None
    passport_no: str | None = None


class BookingCreateTicketingResponse(BaseModel):
    status: str | None = None
    time_limit: str | None = None
    ticket_numbers: list[str] = Field(default_factory=list)


class BookingCreateSummaryResponse(BaseModel):
    pnr: str | None = None
    status: str | None = None
    status_code: str | None = None
    created_at: str | None = None
    contact: BookingCreateContactResponse
    passengers: list[BookingCreatePassengerResponse] = Field(default_factory=list)
    ticketing: BookingCreateTicketingResponse


class BookingCreateResponse(BaseModel):
    booking_reference: str | None = None
    summary: BookingCreateSummaryResponse
