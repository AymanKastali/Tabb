"""In-memory outbox processor with retry and dead-lettering."""

from __future__ import annotations

from tabb.application.ports.inbound.outbox_processor import OutboxProcessor
from tabb.application.ports.inbound.projector import Projector
from tabb.application.ports.outbound.logger import LoggerPort
from tabb.application.ports.outbound.outbox_repository import OutboxRepository


class InMemoryOutboxProcessor(OutboxProcessor):
    """Processes pending outbox entries by dispatching to registered projectors.

    1. Polls outbox_repository.find_pending(limit)
    2. For each entry, finds a projector that handles the event_type
    3. On success: mark_processed
    4. On failure: mark_failed (increments retry_count)
    5. When retry_count >= max_retries: entry becomes DEAD_LETTERED
    """

    def __init__(
        self,
        outbox_repository: OutboxRepository,
        projectors: list[Projector],
        logger: LoggerPort | None = None,
    ) -> None:
        self._outbox_repo = outbox_repository
        self._projector_map: dict[str, Projector] = {}
        self._logger = logger
        for projector in projectors:
            for event_type in projector.handles():
                self._projector_map[event_type] = projector

    async def process_pending(self) -> int:
        """Process pending outbox entries. Returns count of successfully processed."""
        entries = await self._outbox_repo.find_pending(limit=10)
        processed_count = 0

        for entry in entries:
            projector = self._projector_map.get(entry.event_type)
            if projector is None:
                error_msg = (
                    f"No projector registered for event type: {entry.event_type}"
                )
                await self._outbox_repo.mark_failed(entry.entry_id, error_msg)
                self._log_failure(
                    entry.entry_id, entry.retry_count, entry.max_retries, error_msg
                )
                continue

            try:
                await projector.project(entry.event_type, entry.event_data)
                await self._outbox_repo.mark_processed(entry.entry_id)
                processed_count += 1
                if self._logger:
                    self._logger.debug("Outbox entry processed: %s", entry.entry_id)
            except Exception as exc:
                await self._outbox_repo.mark_failed(entry.entry_id, str(exc))
                self._log_failure(
                    entry.entry_id, entry.retry_count, entry.max_retries, str(exc)
                )

        return processed_count

    def _log_failure(
        self,
        entry_id: str,
        retry_count: int,
        max_retries: int,
        error: str,
    ) -> None:
        if not self._logger:
            return
        if retry_count >= max_retries:
            self._logger.warning("Outbox entry dead-lettered: %s — %s", entry_id, error)
        else:
            self._logger.info(
                "Outbox entry failed (retry %d/%d): %s — %s",
                retry_count,
                max_retries,
                entry_id,
                error,
            )
