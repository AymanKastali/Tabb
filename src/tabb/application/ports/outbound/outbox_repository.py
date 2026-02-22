"""Outbound port — outbox repository for the transactional outbox pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod

from tabb.application.outbox import OutboxEntry


class OutboxRepository(ABC):
    """Abstract repository for outbox entry persistence."""

    @abstractmethod
    async def save(self, entry: OutboxEntry) -> None:
        """Persist an outbox entry."""

    @abstractmethod
    async def find_pending(self, limit: int = 10) -> list[OutboxEntry]:
        """Return pending or failed (retryable) entries, ordered by occurred_at."""

    @abstractmethod
    async def mark_processed(self, entry_id: str) -> None:
        """Mark an outbox entry as processed."""

    @abstractmethod
    async def mark_failed(self, entry_id: str, error: str) -> None:
        """Mark an outbox entry as failed with an error message."""

    @abstractmethod
    async def mark_dead_lettered(self, entry_id: str) -> None:
        """Mark an outbox entry as dead-lettered (exhausted retries)."""
