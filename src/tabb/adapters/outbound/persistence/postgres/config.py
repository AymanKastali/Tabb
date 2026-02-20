"""Database configuration and dependency provider for tabb."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from tabb.adapters.outbound.persistence.postgres.database import PostgresDatabase

database = PostgresDatabase()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session (FastAPI dependency)."""
    async with database.session() as session:
        yield session
