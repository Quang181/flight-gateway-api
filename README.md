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
├── bootstrap.py
├── application/
│   └── use_cases/
│       └── get_health_status.py
├── domain/
│   └── ports/
│       └── health_repository.py
├── entrypoints/
│   └── api/
│       ├── decorators.py
│       ├── dependencies.py
│       ├── middlewares/
│           └── auth.py
│       └── routers/
│           ├── __init__.py
│           └── system/
│               ├── __init__.py
│               ├── health.py
│               └── secure.py
└── infrastructure/
    ├── lifecycle.py
    ├── cache/
    │   └── redis.py
    ├── config/
    │   └── settings.py
    ├── db/
    │   └── postgres.py
    └── repositories/
        └── health_repository.py
```

### File Purpose

- `app/bootstrap.py`: creates the FastAPI app, registers middleware, routes, and lifespan handling.
- `app/application/use_cases/get_health_status.py`: use case layer. Contains the logic for reading dependency health status from an abstract repository.
- `app/domain/ports/health_repository.py`: domain contract. Defines the interface that infrastructure must implement.
- `app/entrypoints/api/routers/__init__.py`: router aggregator. Combines router groups into one `api_router`.
- `app/entrypoints/api/routers/system/__init__.py`: declares the shared `APIRouter(tags=["system"])` for the whole system group and imports endpoint modules in that group.
- `app/entrypoints/api/routers/system/health.py`: system endpoints related to health checks such as `/health`. This file reuses the shared router from the same folder.
- `app/entrypoints/api/routers/system/secure.py`: protected system endpoints such as `/secure/ping`. This file also reuses the shared router from the same folder.
- `app/entrypoints/api/dependencies.py`: FastAPI dependency wiring. Builds use case instances from objects stored in `app.state`.
- `app/entrypoints/api/decorators.py`: route-level decorators, currently used to mark endpoints that require token authentication.
- `app/entrypoints/api/middlewares/auth.py`: request middleware that checks the configured token for protected endpoints.
- `app/infrastructure/config/settings.py`: loads and validates configuration from `env.yaml`.
- `app/infrastructure/lifecycle.py`: startup and shutdown flow. Initializes PostgreSQL, Redis, and shared app state.
- `app/infrastructure/db/postgres.py`: PostgreSQL connection manager and health check implementation.
- `app/infrastructure/cache/redis.py`: Redis connection manager and health check implementation.
- `app/infrastructure/repositories/health_repository.py`: concrete implementation of the domain repository using PostgreSQL and Redis.

### How The Layers Work Together

1. `main.py` starts the app.
2. `app/bootstrap.py` creates the FastAPI instance.
3. `app/infrastructure/lifecycle.py` initializes external dependencies and stores them in `app.state`.
4. `app/entrypoints/api/routers/<group>/__init__.py` defines the shared router for a tag group.
5. Endpoint files inside the same router group import that shared router and register their own paths.
6. `app/entrypoints/api/dependencies.py` builds use cases for the route.
7. `app/application/use_cases/get_health_status.py` calls the repository through the domain port.
8. `app/infrastructure/repositories/health_repository.py` talks to PostgreSQL and Redis through the infrastructure managers.

## Environment

All application config is loaded from `env.yaml` under the `flight_gateway` prefix:

```yaml
flight_gateway:
  app_name: flight-gateway-api
  app_host: 0.0.0.0
  app_port: 8000
  database_url: postgresql+asyncpg://postgres:postgres@localhost:5432/flight_gateway
  redis_url: redis://localhost:6379/0
  auth_header_name: X-API-Token
  auth_token: change-me
```

### Config Field Meaning

- `app_name`: FastAPI application title.
- `app_host`: host address the server binds to.
- `app_port`: port the server listens on.
- `database_url`: PostgreSQL connection string used by SQLAlchemy/asyncpg.
- `redis_url`: Redis connection string.
- `auth_header_name`: request header used to carry the token for protected routes.
- `auth_token`: expected token value for protected routes.

## Run

```bash
poetry install
poetry run python main.py
```

## Available Endpoints

- `GET /health`: returns API and dependency status. If PostgreSQL or Redis is down, the API still starts and reports a degraded status.
- `GET /secure/ping`: protected endpoint that requires the configured token in the header defined by `auth_header_name`.
