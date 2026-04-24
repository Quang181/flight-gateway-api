from sqlalchemy.engine import make_url


def build_migration_database_url(async_database_url: str) -> str:
    url = make_url(async_database_url)
    return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)
