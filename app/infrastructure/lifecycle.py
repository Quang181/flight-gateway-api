from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.infrastructure.cache.redis import RedisManager
from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.postgres import PostgresManager
from app.infrastructure.repositories.health_repository import DependencyHealthRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    postgres = PostgresManager(settings.database_url)
    redis = RedisManager(settings.redis_url)

    try:
        await postgres.connect()
    except Exception as exc:
        logger.warning("PostgreSQL is unavailable during startup: %s", exc)

    try:
        await redis.connect()
    except Exception as exc:
        logger.warning("Redis is unavailable during startup: %s", exc)

    app.state.postgres = postgres
    app.state.redis = redis
    app.state.health_repository = DependencyHealthRepository(postgres=postgres, redis=redis)

    try:
        yield
    finally:
        await redis.disconnect()
        await postgres.disconnect()
