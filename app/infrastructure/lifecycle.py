from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.infrastructure.apicall import MockTravelFlightApiClient
from app.infrastructure.cache.flight import FlightRedisCache
from app.infrastructure.cache.redis import RedisManager
from app.infrastructure.config.settings import get_settings
from app.infrastructure.db.postgres import PostgresManager
from app.infrastructure.repositories.flight_repository import MockTravelFlightRepository
from app.infrastructure.repositories.health_repository import DependencyHealthRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    postgres = PostgresManager(settings.database_url)
    redis = RedisManager(settings.redis_url)
    flight_api_client = MockTravelFlightApiClient(
        base_url=settings.mock_travel_api_url,
        timeout=settings.legacy_api_timeout_seconds,
        max_retries=settings.legacy_api_retry_count,
        backoff_seconds=settings.legacy_api_backoff_seconds,
        default_headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    flight_cache = FlightRedisCache(redis=redis)
    flight_repository = MockTravelFlightRepository(api_client=flight_api_client, cache=flight_cache)

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
    app.state.flight_repository = flight_repository

    try:
        yield
    finally:
        await flight_api_client.aclose()
        await redis.disconnect()
        await postgres.disconnect()
