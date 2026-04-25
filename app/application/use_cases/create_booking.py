from typing import Any
from datetime import datetime

from app.application.common.legacy_normalization import normalize_booking
from app.application.common.upstream_errors import map_external_api_error
from app.domain.ports.booking_repository import BookingRepository
from app.domain.ports.flight_repository import FlightRepository
from app.entrypoints.api.errors.exceptions import AppBadRequestError, AppNotFoundError
from app.infrastructure.apicall.base import ExternalApiResponseError


class CreateBooking:
    def __init__(self, repository: FlightRepository, booking_repository: BookingRepository) -> None:
        self._repository = repository
        self._booking_repository = booking_repository

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._validate_payload(payload)
        await self._validate_offer_ids(payload)

        outbound_result = await self._create_legacy_booking(payload, payload["offer_id_outbound"])

        inbound_result: dict[str, Any] | None = None
        if payload["trip_type"] == "round_trip":
            inbound_result = await self._create_legacy_booking(payload, payload["offer_id_inbound"])

        await self._booking_repository.create_booking_record(
            self._build_booking_record(payload, outbound_result, inbound_result)
        )

        booking = normalize_booking(data=outbound_result, method="POST")
        return booking

    async def _validate_offer_ids(self, payload: dict[str, Any]) -> None:
        outbound_metadata = await self._ensure_offer_metadata(
            offer_id=payload["offer_id_outbound"],
            message_key="offer_id_outbound_not_found",
            code="OFFER_ID_OUTBOUND_NOT_FOUND",
            expected_direction="outbound",
            invalid_direction_message_key="offer_id_outbound_invalid_direction",
            invalid_direction_code="OFFER_ID_OUTBOUND_INVALID_DIRECTION",
        )

        if payload["trip_type"] == "round_trip":
            inbound_metadata = await self._ensure_offer_metadata(
                offer_id=payload["offer_id_inbound"],
                message_key="offer_id_inbound_not_found",
                code="OFFER_ID_INBOUND_NOT_FOUND",
                expected_direction="inbound",
                invalid_direction_message_key="offer_id_inbound_invalid_direction",
                invalid_direction_code="OFFER_ID_INBOUND_INVALID_DIRECTION",
            )
            if not self._is_reverse_route(outbound_metadata, inbound_metadata):
                raise AppNotFoundError(
                    message_key="offer_id_inbound_invalid_route",
                    code="OFFER_ID_INBOUND_INVALID_ROUTE",
                )
            if not self._is_valid_departure_sequence(outbound_metadata, inbound_metadata):
                raise AppNotFoundError(
                    message_key="offer_departure_sequence_invalid",
                    code="OFFER_DEPARTURE_SEQUENCE_INVALID",
                )

    async def _create_legacy_booking(self, payload: dict[str, Any], offer_id: str) -> dict[str, Any]:
        try:
            result = await self._repository.create_booking(self._build_legacy_payload(payload, offer_id))
        except Exception as exc:
            raise map_external_api_error(exc) from exc
        return result

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        passengers = payload.get("passengers")
        if not payload.get("trip_type"):
            raise AppBadRequestError(message_key="trip_type_required", code="TRIP_TYPE_REQUIRED")

        if not payload.get("offer_id_outbound"):
            raise AppBadRequestError(message_key="offer_id_outbound_required", code="OFFER_ID_OUTBOUND_REQUIRED")

        if payload.get("trip_type") == "round_trip" and not payload.get("offer_id_inbound"):
            raise AppBadRequestError(message_key="offer_id_inbound_required", code="OFFER_ID_INBOUND_REQUIRED")

        if not isinstance(passengers, list) or not passengers:
            raise AppBadRequestError(message_key="passengers_required", code="PASSENGERS_REQUIRED")

    async def _ensure_offer_metadata(
        self,
        offer_id: str,
        message_key: str,
        code: str,
        expected_direction: str,
        invalid_direction_message_key: str,
        invalid_direction_code: str,
    ) -> dict[str, Any]:
        try:
            metadata = await self._repository.get_offer_metadata(offer_id)
        except ExternalApiResponseError as exc:
            raise map_external_api_error(exc) from exc
        except Exception as exc:
            raise map_external_api_error(exc) from exc

        if not isinstance(metadata, dict):
            raise AppNotFoundError(message_key=message_key, code=code)
        if metadata.get("direction") != expected_direction:
            raise AppNotFoundError(
                message_key=invalid_direction_message_key,
                code=invalid_direction_code,
            )
        return metadata

    @staticmethod
    def _is_reverse_route(outbound_metadata: dict[str, Any], inbound_metadata: dict[str, Any]) -> bool:
        outbound_origin = outbound_metadata.get("origin")
        outbound_destination = outbound_metadata.get("destination")
        inbound_origin = inbound_metadata.get("origin")
        inbound_destination = inbound_metadata.get("destination")
        return (
            isinstance(outbound_origin, str)
            and isinstance(outbound_destination, str)
            and isinstance(inbound_origin, str)
            and isinstance(inbound_destination, str)
            and outbound_origin == inbound_destination
            and outbound_destination == inbound_origin
        )

    @classmethod
    def _is_valid_departure_sequence(cls, outbound_metadata: dict[str, Any], inbound_metadata: dict[str, Any]) -> bool:
        outbound_departure = cls._parse_departure_at(outbound_metadata.get("departure_at"))
        inbound_departure = cls._parse_departure_at(inbound_metadata.get("departure_at"))
        if outbound_departure is None or inbound_departure is None:
            return False
        return outbound_departure < inbound_departure

    @staticmethod
    def _parse_departure_at(value: Any) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _build_legacy_payload(payload: dict[str, Any], offer_id: str) -> dict[str, Any]:
        contact = payload.get("contact", {})
        return {
            "offer_id": offer_id,
            "passengers": payload["passengers"],
            "contact_email": contact.get("email"),
            "contact_phone": contact.get("phone"),
        }

    @staticmethod
    def _build_booking_record(
        payload: dict[str, Any],
        outbound_result: dict[str, Any],
        inbound_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        outbound_data = outbound_result.get("data", {})
        inbound_data = inbound_result.get("data", {}) if isinstance(inbound_result, dict) else {}
        return {
            "booking_reference": outbound_data.get("booking_ref"),
            "trip_type": payload["trip_type"],
            "outbound_offer_id": payload["offer_id_outbound"],
            "inbound_offer_id": payload.get("offer_id_inbound"),
            "outbound_booking_ref": outbound_data.get("booking_ref"),
            "inbound_booking_ref": inbound_data.get("booking_ref"),
            "status": "confirmed",
        }
