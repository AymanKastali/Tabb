"""Async background outbox worker adapter."""

from __future__ import annotations

import asyncio

from tabb.application.ports.inbound.outbox_processor import OutboxProcessor
from tabb.application.ports.inbound.outbox_worker import OutboxWorker
from tabb.application.ports.outbound.logger import LoggerPort


class AsyncOutboxWorker(OutboxWorker):
    """Periodically polls the outbox processor using an asyncio background task."""

    def __init__(
        self,
        processor: OutboxProcessor,
        interval_seconds: float = 1.0,
        logger: LoggerPort | None = None,
    ) -> None:
        self._processor = processor
        self._interval = interval_seconds
        self._logger = logger
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the background polling loop. Idempotent."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        if self._logger:
            self._logger.info("Outbox worker started")

    async def stop(self) -> None:
        """Stop the background polling loop and wait for cleanup."""
        if not self._running:
            return
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._logger:
            self._logger.info("Outbox worker stopped")

    async def _poll_loop(self) -> None:
        """Run process_pending in a loop until stopped."""
        while self._running:
            try:
                await self._processor.process_pending()
            except Exception as exc:
                if self._logger:
                    self._logger.error("Outbox worker poll error: %s", exc)
            await asyncio.sleep(self._interval)
