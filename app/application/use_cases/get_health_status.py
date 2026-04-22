from app.domain.ports.health_repository import HealthRepository


class GetHealthStatus:
    def __init__(self, repository: HealthRepository) -> None:
        self._repository = repository

    async def execute(self) -> dict[str, str]:
        return await self._repository.ping()
