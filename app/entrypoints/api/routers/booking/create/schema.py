import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.entrypoints.api.errors.exceptions import AppValidationError


EMAIL_REGEX = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
PHONE_REGEX = re.compile(r"^\d{8,20}$")
PASSPORT_REGEX = re.compile(r"^[A-Z0-9]{6,20}$", re.IGNORECASE)



class BookingPassenger(BaseModel):
    title: str = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    dob: str = Field(...)
    nationality: str = Field(...)
    passport_no: str = Field(...)
    email: str = Field(...)
    phone: str = Field(...)

    @model_validator(mode="before")
    @classmethod
    def validate_required_fields(cls, value: object) -> object:
        payload = _ensure_dict(value, "passengers", "PASSENGERS_INVALID")
        for field_name in (
            "title",
            "first_name",
            "last_name",
            "dob",
            "nationality",
            "passport_no",
            "email",
            "phone",
        ):
            _require_non_empty_string(payload.get(field_name), f"{field_name.upper()}_REQUIRED")
        return payload

    @field_validator("passport_no")
    @classmethod
    def validate_passport_no(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 6 or len(normalized) > 20 or not PASSPORT_REGEX.fullmatch(normalized):
            raise AppValidationError(
                message_key="passport_no_invalid",
                code="PASSPORT_NO_INVALID",
            )
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip()
        if not EMAIL_REGEX.fullmatch(normalized):
            raise AppValidationError(message_key="email_invalid", code="EMAIL_INVALID")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not PHONE_REGEX.fullmatch(normalized):
            raise AppValidationError(message_key="phone_invalid", code="PHONE_INVALID")
        return normalized

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, value: str) -> str:
        normalized = value.strip()
        try:
            parsed = date.fromisoformat(normalized)
        except ValueError as exc:
            raise AppValidationError(
                message_key="dob_invalid_format",
                code="DOB_INVALID",
            ) from exc
        minimum_age_in_days = 14
        age_in_days = (date.today() - parsed).days
        if age_in_days < minimum_age_in_days:
            raise AppValidationError(
                message_key="dob_too_young",
                code="DOB_INVALID",
            )
        return parsed.isoformat()


class BookingContact(BaseModel):
    email: str = Field(...)
    phone: str = Field(...)

    @model_validator(mode="before")
    @classmethod
    def validate_required_fields(cls, value: object) -> object:
        payload = _ensure_dict(value, "contact", "CONTACT_INVALID")
        _require_non_empty_string(payload.get("email"), "CONTACT_EMAIL_REQUIRED")
        _require_non_empty_string(payload.get("phone"), "CONTACT_PHONE_REQUIRED")
        return payload

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip()
        if not EMAIL_REGEX.fullmatch(normalized):
            raise AppValidationError(message_key="email_invalid", code="CONTACT_EMAIL_INVALID")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not PHONE_REGEX.fullmatch(normalized):
            raise AppValidationError(message_key="phone_invalid", code="CONTACT_PHONE_INVALID")
        return normalized


class BookingCreateRequest(BaseModel):
    trip_type: Literal["one_way", "round_trip"] = Field(...)
    offer_id_outbound: str = Field(...)
    offer_id_inbound: str | None = None
    passengers: list[BookingPassenger] = Field(...)
    contact: BookingContact

    @model_validator(mode="before")
    @classmethod
    def validate_payload(cls, value: object) -> object:
        payload = _ensure_dict(value, "payload", "BOOKING_CREATE_PAYLOAD_INVALID")
        _require_non_empty_string(payload.get("trip_type"), "TRIP_TYPE_REQUIRED")
        _require_non_empty_string(payload.get("offer_id_outbound"), "OFFER_ID_OUTBOUND_REQUIRED")

        trip_type = payload.get("trip_type")
        inbound_offer_id = payload.get("offer_id_inbound")
        if trip_type == "one_way":
            if inbound_offer_id not in (None, ""):
                raise AppValidationError(
                    message_key="offer_id_inbound_not_allowed",
                    code="OFFER_ID_INBOUND_NOT_ALLOWED",
                )
        elif trip_type == "round_trip":
            _require_non_empty_string(inbound_offer_id, "OFFER_ID_INBOUND_REQUIRED")

        passengers = payload.get("passengers")
        if not isinstance(passengers, list) or not passengers:
            raise AppValidationError(
                message_key="passengers_required",
                code="PASSENGERS_REQUIRED",
            )

        for index, passenger in enumerate(passengers):
            try:
                BookingPassenger.model_validate(passenger)
            except AppValidationError as exc:
                raise AppValidationError(
                    message_key=exc.message_key,
                    code=_prefix_code(f"PASSENGERS_{index}", exc.code),
                ) from exc

        try:
            BookingContact.model_validate(payload.get("contact"))
        except AppValidationError as exc:
            raise AppValidationError(
                message_key=exc.message_key,
                code=exc.code,
            ) from exc

        return payload

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
                raise AppValidationError(
                    message_key="passengers_email_duplicate",
                    code="PASSENGERS_EMAIL_DUPLICATE",
                )
            if phone in seen_phones:
                raise AppValidationError(
                    message_key="passengers_phone_duplicate",
                    code="PASSENGERS_PHONE_DUPLICATE",
                )
            if passport_no in seen_passport_numbers:
                raise AppValidationError(
                    message_key="passengers_passport_no_duplicate",
                    code="PASSENGERS_PASSPORT_NO_DUPLICATE",
                )

            seen_emails.add(email)
            seen_phones.add(phone)
            seen_passport_numbers.add(passport_no)

        return self


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


def _ensure_dict(value: object, field_name: str, code: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AppValidationError(
            message_key="invalid_object",
            code=code,
        )
    return value


def _require_non_empty_string(value: object, code: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AppValidationError(
            message_key="field_required",
            code=code,
        )


def _prefix_code(prefix: str, code: str | None) -> str:
    if not code:
        return prefix
    return f"{prefix}_{code}"
