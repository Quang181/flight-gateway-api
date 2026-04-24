from typing import Any

from app.application.common.legacy_normalization import normalize_booking
from app.application.common.upstream_errors import map_external_api_error
from app.domain.ports.flight_repository import FlightRepository
from app.entrypoints.api.errors.exceptions import AppBadRequestError, AppNotFoundError
from app.infrastructure.apicall.base import ExternalApiResponseError


class CreateBooking:
    def __init__(self, repository: FlightRepository) -> None:
        self._repository = repository

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._validate_payload(payload)
        await self._ensure_offer_exists(payload["offer_id"])
        try:
            result = await self._repository.create_booking(payload)
        except Exception as exc:
            raise map_external_api_error(exc) from exc
        booking = normalize_booking(data=result,
                                    method="POST")

        return booking

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        passengers = payload.get("passengers")
        if not payload.get("offer_id"):
            raise AppBadRequestError(message_key="offer_id_required", code="OFFER_ID_REQUIRED")

        if not payload.get("contact_email"):
            raise AppBadRequestError(message_key="contact_email_required", code="CONTACT_EMAIL_REQUIRED")

        if not payload.get("contact_phone"):
            raise AppBadRequestError(message_key="contact_phone_required", code="CONTACT_PHONE_REQUIRED")

        if not isinstance(passengers, list) or not passengers:
            raise AppBadRequestError(message_key="passengers_required", code="PASSENGERS_REQUIRED")

    async def _ensure_offer_exists(self, offer_id: str) -> None:
        try:
            await self._repository.get_offer_detail(offer_id)
        except ExternalApiResponseError as exc:
            if exc.status_code == 404:
                raise AppNotFoundError(message_key="offer_id_not_found", code="OFFER_ID_NOT_FOUND") from exc

            raise map_external_api_error(exc) from exc
        except Exception as exc:
            raise map_external_api_error(exc) from exc
