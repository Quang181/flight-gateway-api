from abc import ABC, abstractmethod
from typing import Any


class FlightRepository(ABC):
    @abstractmethod
    async def get_airports(self) -> dict[str, Any]:
        """Retrieve airport catalog from an external provider."""

    @abstractmethod
    async def get_airport_detail(self, code: str) -> dict[str, Any]:
        """Retrieve airport detail by code from an external provider."""

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

    @abstractmethod
    async def set_offer_metadata(self, offer_id: str, value: dict[str, Any], ttl_seconds: int) -> None:
        """Store cached metadata for a single flight offer."""

    @abstractmethod
    async def get_offer_metadata(self, offer_id: str) -> dict[str, Any] | None:
        """Retrieve cached metadata for a single flight offer."""
