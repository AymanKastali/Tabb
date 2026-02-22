"""Inbound port — CQRS query abstractions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, kw_only=True)
class Query:
    """Base class for all queries. Queries are immutable data carriers."""


class QueryHandler(ABC):
    """Handles a single query type."""

    @abstractmethod
    async def handle(self, query: Query) -> Any:
        """Execute the query and return a result."""


class QueryBus(ABC):
    """Dispatches queries to their registered handlers."""

    @abstractmethod
    async def dispatch(self, query: Query) -> Any:
        """Route a query to the appropriate handler and return the result."""
