from app.infrastructure.db.alembic import build_migration_database_url


def test_build_migration_database_url_switches_asyncpg_to_psycopg() -> None:
    runtime_url = "postgresql+asyncpg://postgres:123456@localhost:5432/flight_gateway"

    migration_url = build_migration_database_url(runtime_url)

    assert migration_url == "postgresql+psycopg://postgres:123456@localhost:5432/flight_gateway"
