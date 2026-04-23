from typing import Any

from app.application.common.legacy_normalization import normalize_offer_detail
from app.application.common.upstream_errors import map_external_api_error
from app.domain.ports.flight_repository import FlightRepository


class GetOfferDetail:
    def __init__(self, repository: FlightRepository) -> None:
        self._repository = repository

    async def execute(self, offer_id: str) -> dict[str, Any]:
        try:
            result = await self._repository.get_offer_detail(offer_id)
        except Exception as exc:
            raise map_external_api_error(exc) from exc
        return normalize_offer_detail(result)
