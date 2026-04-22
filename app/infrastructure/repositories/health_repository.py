from app.domain.ports.health_repository import HealthRepository
from app.infrastructure.cache.redis import RedisManager
from app.infrastructure.db.postgres import PostgresManager


class DependencyHealthRepository(HealthRepository):
    def __init__(self, postgres: PostgresManager, redis: RedisManager) -> None:
        self._postgres = postgres
        self._redis = redis

    async def ping(self) -> dict[str, str]:
        postgres_status = await self._safe_ping(self._postgres.ping)
        redis_status = await self._safe_ping(self._redis.ping)
        return {"postgres": postgres_status, "redis": redis_status}

    @staticmethod
    async def _safe_ping(check) -> str:
        try:
            return await check()
        except Exception:
            return "unavailable"
