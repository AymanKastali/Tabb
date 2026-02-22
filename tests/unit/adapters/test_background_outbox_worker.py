"""Unit tests for AsyncOutboxWorker lifecycle."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from tabb.adapters.outbound.workers.background_outbox_worker import AsyncOutboxWorker

pytestmark = pytest.mark.asyncio


def _make_processor(side_effect: Exception | None = None) -> AsyncMock:
    processor = AsyncMock()
    processor.process_pending = AsyncMock(return_value=0, side_effect=side_effect)
    return processor


class TestAsyncOutboxWorker:
    async def test_start_polls_processor(self):
        processor = _make_processor()
        worker = AsyncOutboxWorker(processor=processor, interval_seconds=0.05)

        await worker.start()
        await asyncio.sleep(0.15)
        await worker.stop()

        assert processor.process_pending.call_count >= 2

    async def test_stop_cancels_cleanly(self):
        processor = _make_processor()
        worker = AsyncOutboxWorker(processor=processor, interval_seconds=0.05)

        await worker.start()
        await asyncio.sleep(0.05)
        await worker.stop()

        # No lingering tasks — worker task is None after stop
        assert worker._task is None

    async def test_start_is_idempotent(self):
        processor = _make_processor()
        worker = AsyncOutboxWorker(processor=processor, interval_seconds=0.05)

        await worker.start()
        task1 = worker._task
        await worker.start()  # Second call should be no-op
        task2 = worker._task

        assert task1 is task2
        await worker.stop()

    async def test_poll_survives_processor_exception(self):
        processor = _make_processor(side_effect=RuntimeError("boom"))
        worker = AsyncOutboxWorker(processor=processor, interval_seconds=0.05)

        await worker.start()
        await asyncio.sleep(0.15)
        await worker.stop()

        # Worker kept polling despite exceptions
        assert processor.process_pending.call_count >= 2
