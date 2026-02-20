"""Outbound port — database connection interface for tabb.

Defines the abstract contract for database connectivity.
Concrete implementations live in the adapters layer.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any


class DatabasePort(ABC):
    """Abstract database connection interface (outbound port)."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish the database connection / initialize the connection pool."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully close all connections and dispose of the connection pool."""

    @abstractmethod
    async def ping(self) -> bool:
        """Check database connectivity. Returns True if reachable."""

    @abstractmethod
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[Any, None]:
        """Provide a transactional database session as an async context manager."""
        yield  # pragma: no cover
