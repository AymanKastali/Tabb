"""In-memory Outbox repository adapter with staged writes for UoW."""

from __future__ import annotations

import copy

from tabb.application.outbox import OutboxEntry, OutboxEntryStatus
from tabb.application.ports.outbound.outbox_repository import OutboxRepository


class InMemoryOutboxRepository(OutboxRepository):
    """In-memory repository for outbox entries.

    Supports staged writes for UoW integration.
    """

    def __init__(self, store: list[OutboxEntry]) -> None:
        self._store = store
        self._staging: list[OutboxEntry] = []

    async def save(self, entry: OutboxEntry) -> None:
        self._staging.append(copy.deepcopy(entry))

    async def find_pending(self, limit: int = 10) -> list[OutboxEntry]:
        """Return pending or failed (retryable) entries from the committed store."""
        pending = [
            e
            for e in self._store
            if e.status in (OutboxEntryStatus.PENDING, OutboxEntryStatus.FAILED)
            and e.can_retry
            and e.is_ready_for_retry
        ]
        pending.sort(key=lambda e: e.occurred_at)
        return pending[:limit]

    async def mark_processed(self, entry_id: str) -> None:
        for entry in self._store:
            if entry.entry_id == entry_id:
                entry.mark_processed()
                return

    async def mark_failed(self, entry_id: str, error: str) -> None:
        for entry in self._store:
            if entry.entry_id == entry_id:
                entry.mark_failed(error)
                return

    async def mark_dead_lettered(self, entry_id: str) -> None:
        for entry in self._store:
            if entry.entry_id == entry_id:
                entry._status = OutboxEntryStatus.DEAD_LETTERED
                return

    def flush(self) -> None:
        """Apply staged writes to the committed store."""
        self._store.extend(self._staging)
        self._staging.clear()

    def discard(self) -> None:
        """Discard staged writes."""
        self._staging.clear()
