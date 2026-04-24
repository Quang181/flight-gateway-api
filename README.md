# Flight Gateway API

Hexagonal FastAPI scaffold with PostgreSQL, Redis, and conditional token middleware.

## Project Structure

This project follows a simple hexagonal architecture. The code is split into `domain`, `application`, `infrastructure`, and `entrypoints` so business logic is separated from framework and external services.

### Root Files

- `main.py`: application entrypoint used to run the API server.
- `env.yaml`: central configuration file. All runtime settings are loaded from here under the `flight_gateway` prefix.
- `pyproject.toml`: Poetry configuration and dependency definition.
- `poetry.lock`: locked dependency versions for reproducible installs.
- `README.md`: project guide, run instructions, and code structure overview.

### Application Tree

```text
app/
├── __init__.py
├── bootstrap.py
├── application/
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── constant.py
│   │   ├── legacy_normalization.py
│   │   ├── pagination.py
│   │   └── upstream_errors.py
│   └── use_cases/
│       ├── __init__.py
│       ├── create_booking.py
│       ├── get_booking.py
│       ├── get_offer_detail.py
│       └── list_flights.py
├── domain/
│   ├── __init__.py
│   └── ports/
│       ├── __init__.py
│       └── flight_repository.py
├── entrypoints/
│   ├── __init__.py
│   └── api/
│       ├── __init__.py
│       ├── decorators.py
│       ├── dependencies.py
│       ├── errors/
│       │   ├── __init__.py
│       │   ├── exceptions.py
│       │   ├── handlers.py
│       │   ├── langs/
│       │   │   ├── en.json
│       │   │   └── vi.json
│       │   ├── responses.py
│       │   └── translations.py
│       ├── middlewares/
│       │   ├── __init__.py
│       │   └── auth.py
│       └── routers/
│           ├── __init__.py
│           ├── booking/
│           │   ├── __init__.py
│           │   ├── create/
│           │   │   ├── __init__.py
│           │   │   ├── router.py
│           │   │   └── schema.py
│           │   └── detail/
│           │       ├── __init__.py
│           │       ├── router.py
│           │       └── schema.py
│           └── flight/
│               ├── __init__.py
│               ├── list/
│               │   ├── __init__.py
│               │   ├── router.py
│               │   └── schema.py
│               └── offer/
│                   ├── __init__.py
│                   ├── router.py
│                   └── schema.py
└── infrastructure/
    ├── __init__.py
    ├── airlines/
    │   ├── __init__.py
    │   └── catalog.py
    ├── apicall/
    │   ├── __init__.py
    │   ├── base.py
    │   └── flight_search.py
    ├── cache/
    │   ├── __init__.py
    │   ├── flight.py
    │   └── redis.py
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    ├── data/
    │   └── airlines.json
    ├── db/
    │   ├── __init__.py
    │   ├── alembic.py
    │   ├── models.py
    │   └── postgres.py
    ├── lifecycle.py
    └── repositories/
        ├── __init__.py
        └── flight_repository.py
```

### File Purpose

- `app/bootstrap.py`: creates the FastAPI app, registers middleware, routes, and lifespan handling.
- `app/application/common/constant.py`: shared constants for the application layer, such as reusable regex patterns.
- `app/application/use_cases/list_flights.py`: use case for searching flights through the outbound flight repository port.
- `app/domain/ports/flight_repository.py`: domain contract for outbound flight search integrations.
- `app/entrypoints/api/routers/__init__.py`: router aggregator. Combines router groups into one `api_router`.
- `app/entrypoints/api/routers/flight/__init__.py`: declares the shared flight router group and includes child routers.
- `app/entrypoints/api/routers/flight/list/schema.py`: request query schema for the `GET /flights/flight` endpoint.
- `app/entrypoints/api/routers/flight/list/router.py`: flight list endpoint that validates query params and dispatches to the use case.
- `app/entrypoints/api/dependencies.py`: FastAPI dependency wiring. Builds use case instances from objects stored in `app.state`.
- `app/entrypoints/api/decorators.py`: route-level decorators, currently used to mark endpoints that require token authentication.
- `app/entrypoints/api/middlewares/auth.py`: request middleware that checks the configured token for protected endpoints.
- `app/infrastructure/apicall/base.py`: reusable base HTTP client for outbound API adapters.
- `app/infrastructure/apicall/flight_search.py`: concrete outbound adapter for the mock travel flight search API.
- `app/infrastructure/airlines/catalog.py`: loads airline code to airline name mappings from JSON at startup.
- `app/infrastructure/config/settings.py`: loads and validates configuration from `env.yaml`.
- `app/infrastructure/data/airlines.json`: preload data source for airline code to airline name mapping.
- `app/infrastructure/lifecycle.py`: startup and shutdown flow. Initializes PostgreSQL, Redis, and shared app state.
- `app/infrastructure/db/postgres.py`: PostgreSQL connection manager.
- `app/infrastructure/cache/redis.py`: Redis connection manager.

### How The Layers Work Together

1. `main.py` starts the app.
2. `app/bootstrap.py` creates the FastAPI instance.
3. `app/infrastructure/lifecycle.py` initializes external dependencies and stores them in `app.state`.
4. The startup flow also reads `app/infrastructure/data/airlines.json` and stores the airline mapping in memory.
5. `app/entrypoints/api/routers/<group>/__init__.py` defines the shared router for a tag group.
6. Endpoint files inside the same router group import that shared router and register their own paths.
7. `app/entrypoints/api/dependencies.py` builds use cases for the route.
8. `app/application/use_cases/*.py` orchestrate business flow through domain ports.
9. `app/infrastructure/repositories/*.py` and `app/infrastructure/apicall/*.py` implement those ports for databases, cache, and external APIs.

## Environment

All application config is loaded from `env.yaml` under the `flight_gateway` prefix:

```yaml
flight_gateway:
  app_name: flight-gateway-api
  app_host: 0.0.0.0
  app_port: 8000
  database_url: postgresql+asyncpg://postgres:123456@localhost:5432/flight_gateway
  redis_url: redis://localhost:6379/0
  legacy_api_timeout_seconds: 10.0
  legacy_api_retry_count: 2
  legacy_api_backoff_seconds: 0.25
  auth_header_name: X-API-Token
  auth_token: change-me
```

### Config Field Meaning

- `app_name`: FastAPI application title.
- `app_host`: host address the server binds to.
- `app_port`: port the server listens on.
- `database_url`: PostgreSQL connection string used by SQLAlchemy/asyncpg.
- `redis_url`: Redis connection string.
- `legacy_api_timeout_seconds`: timeout for each request sent to the legacy/mock travel API.
- `legacy_api_retry_count`: number of retries after the first failed attempt when the error is retryable.
- `legacy_api_backoff_seconds`: base delay used for exponential backoff between retries.
- `auth_header_name`: request header used to carry the token for protected routes.
- `auth_token`: expected token value for protected routes.

## Retry Behavior

Outbound calls through `app/infrastructure/apicall/base.py` retry only for temporary upstream failures.

- Retry when the upstream request times out (`httpx.TimeoutException`).
- Retry when the upstream returns `429 Too Many Requests`.
- Retry when the upstream returns `503 Service Unavailable`.
- Do not retry for other HTTP statuses such as `400`, `404`, or `502`.
- Do not retry when the upstream returns invalid JSON.
- Do not retry for other network/client errors that fall into generic `httpx.HTTPError`.

Default retry settings:

- `legacy_api_retry_count = 2`: up to 2 retries after the first failed call, so at most 3 total attempts.
- `legacy_api_backoff_seconds = 0.25`: exponential backoff delay of `0.25s`, then `0.5s` before the next retries.
- `legacy_api_timeout_seconds = 10.0`: each individual upstream attempt times out after 10 seconds.

## Run

### Start PostgreSQL And Redis

Run local dependencies with Docker Compose:

```bash
docker compose up -d
```

This starts:

- PostgreSQL at `localhost:5432`
- Redis at `localhost:6379`

The PostgreSQL container is configured for local development with password `123456`, so `database_url` can be:

```yaml
database_url: postgresql+asyncpg://postgres:123456@localhost:5432/flight_gateway
```

To stop the containers:

```bash
docker compose down
```

To stop and remove persisted data volumes:

```bash
docker compose down -v
```

### Install Dependencies

```bash
poetry install
```

### Start The API

```bash
poetry run python main.py
```

### Build And Run With Docker

Build image:

```bash
docker build -t flight-gateway-api .
```

Run container with environment variables:

```bash
docker run -d \
  --name flight-gateway-api \
  -p 8000:8000 \
  -e APP_NAME=flight-gateway-api \
  -e DATABASE_URL=postgresql+asyncpg://postgres:123456@<postgres-host>:5432/flight_gateway \
  -e REDIS_URL=redis://<redis-host>:6379/0 \
  -e MOCK_TRAVEL_API_URL=https://mock-travel-api.vercel.app \
  -e LEGACY_API_TIMEOUT_SECONDS=10.0 \
  -e LEGACY_API_RETRY_COUNT=2 \
  -e LEGACY_API_BACKOFF_SECONDS=0.25 \
  -e AUTH_HEADER_NAME=X-API-Token \
  -e AUTH_TOKEN=change-me \
  flight-gateway-api
```

If your server still manages configuration through `env.yaml`, mount that file into the container instead:

```bash
docker run -d \
  --name flight-gateway-api \
  -p 8000:8000 \
  -v $(pwd)/env.yaml:/app/env.yaml:ro \
  flight-gateway-api
```

The container starts the API with:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Deploy On Server With `env.yaml`

Create `env.yaml` on the server root of this project. When running with Docker Compose, do not use `localhost` for service hosts. Use the Compose service names instead:

```yaml
flight_gateway:
  app_name: flight-gateway-api
  app_host: 0.0.0.0
  app_port: 8000
  database_url: postgresql+asyncpg://postgres:123456@postgres:5432/flight_gateway
  redis_url: redis://redis:6379/0
  mock_travel_api_url: https://mock-travel-api.vercel.app
  legacy_api_timeout_seconds: 10.0
  legacy_api_retry_count: 2
  legacy_api_backoff_seconds: 0.25
  flight_search_cache_ttl_seconds: 300
  booking_cache_ttl_seconds: 300
  auth_header_name: X-API-Token
  auth_token: change-me
```

Start the full stack on the server:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check container status:

```bash
docker compose -f docker-compose.prod.yml ps
```

View app logs:

```bash
docker compose -f docker-compose.prod.yml logs -f app
```

Stop the stack:

```bash
docker compose -f docker-compose.prod.yml down
```

Stop and remove database and Redis data:

```bash
docker compose -f docker-compose.prod.yml down -v
```

### Run Database Migrations

The app keeps using `postgresql+asyncpg://...` at runtime. Alembic automatically converts that URL to `postgresql+psycopg://...` when running migrations.

Create a revision:

```bash
poetry run alembic revision -m "create tables"
```

Apply migrations:

```bash
poetry run alembic upgrade head
```

Show current migration state:

```bash
poetry run alembic current
```

## Available Endpoints
