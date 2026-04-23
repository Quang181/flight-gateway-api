from abc import ABC, abstractmethod
from typing import Any


class FlightRepository(ABC):
    @abstractmethod
    async def search_flights(self, criteria: dict[str, Any]) -> dict[str, Any]:
        """Search flights from an external provider."""

    @abstractmethod
    async def get_offer_detail(self, offer_id: str) -> dict[str, Any]:
        """Retrieve offer details from an external provider."""

    @abstractmethod
    async def create_booking(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a booking with an external provider."""

    @abstractmethod
    async def get_booking(self, reference: str) -> dict[str, Any]:
        """Retrieve a booking from an external provider."""

    @abstractmethod
    async def get(self, key: str) -> dict[str, Any] | None:
        """Get cached flight search result by key."""

    @abstractmethod
    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        """Store flight search result in cache."""
