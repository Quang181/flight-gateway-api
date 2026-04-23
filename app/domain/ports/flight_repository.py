from abc import ABC, abstractmethod
from typing import Any


class FlightRepository(ABC):
    @abstractmethod
    async def search_flights(self, criteria: dict[str, Any]) -> dict[str, Any]:
        """Search flights from an external provider."""

    @abstractmethod
    async def get(self, key: str) -> dict[str, Any] | None:
        """Get cached flight search result by key."""

    @abstractmethod
    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        """Store flight search result in cache."""
