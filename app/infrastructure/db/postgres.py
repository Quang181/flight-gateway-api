from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


class PostgresManager:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

    async def connect(self) -> None:
        async with self._engine.begin() as connection:
            await connection.execute(text("SELECT 1"))

    async def disconnect(self) -> None:
        await self._engine.dispose()

    async def ping(self) -> str:
        async with self._session_factory() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
