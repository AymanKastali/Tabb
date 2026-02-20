"""PostgreSQL database adapter for tabb.

Implements the DatabasePort interface using SQLAlchemy async engine
with asyncpg driver. Manages connection pooling and session lifecycle.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tabb.adapters.config.settings import settings
from tabb.application.ports.outbound.database import DatabasePort
from tabb.adapters.outbound.logging.logger import logger


class PostgresDatabase(DatabasePort):
    """Concrete DatabasePort implementation using SQLAlchemy + asyncpg."""

    def __init__(self) -> None:
        self._engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,
            connect_args={
                "statement_cache_size": 0,
                "command_timeout": settings.db_command_timeout,
            },
        )
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False,
        )

    async def connect(self) -> None:
        """Verify database connectivity on startup."""
        logger.info("Connecting to PostgreSQL...")
        async with self._engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established.")

    async def disconnect(self) -> None:
        """Dispose of the connection pool."""
        logger.info("Closing database connections...")
        await self._engine.dispose()
        logger.info("Database connections closed.")

    async def ping(self) -> bool:
        """Check database connectivity."""
        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            logger.warning("Database ping failed.", exc_info=True)
            return False

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide an async database session."""
        async with self._session_factory() as session:
            yield session
