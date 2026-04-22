from abc import ABC, abstractmethod


class HealthRepository(ABC):
    @abstractmethod
    async def ping(self) -> dict[str, str]:
        """Return dependency health information."""
