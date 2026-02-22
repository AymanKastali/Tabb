"""Unit tests for OutboxEntry exponential backoff."""

from datetime import UTC, datetime, timedelta

from tabb.application.outbox import OutboxEntry, OutboxEntryStatus
from tabb.domain.events.events import MenuItemCreated


def _make_entry() -> OutboxEntry:
    event = MenuItemCreated(
        menu_item_id="m-1",
        name="Burger",
        price="9.99",
    )
    return OutboxEntry.create(
        entry_id="entry-1",
        event=event,
        aggregate_id="m-1",
        aggregate_type="MenuItem",
    )


class TestOutboxEntryBackoff:
    def test_mark_failed_sets_next_retry_at(self):
        entry = _make_entry()

        entry.mark_failed("err")
        assert entry.status == OutboxEntryStatus.FAILED
        assert entry.retry_count == 1
        assert entry.next_retry_at is not None
        # First retry delay: base_delay * 2^0 = 1s
        expected_min = datetime.now(UTC) + timedelta(seconds=0.5)
        expected_max = datetime.now(UTC) + timedelta(seconds=1.5)
        assert expected_min <= entry.next_retry_at <= expected_max

        entry.mark_failed("err2")
        assert entry.retry_count == 2
        assert entry.next_retry_at is not None
        # Second retry delay: base_delay * 2^1 = 2s
        expected_min = datetime.now(UTC) + timedelta(seconds=1.5)
        expected_max = datetime.now(UTC) + timedelta(seconds=2.5)
        assert expected_min <= entry.next_retry_at <= expected_max

    def test_dead_lettered_entry_has_no_next_retry_at(self):
        entry = _make_entry()

        entry.mark_failed("err1")
        entry.mark_failed("err2")
        entry.mark_failed("err3")

        assert entry.status == OutboxEntryStatus.DEAD_LETTERED
        assert entry.next_retry_at is None

    def test_is_ready_for_retry_when_pending(self):
        entry = _make_entry()
        assert entry.status == OutboxEntryStatus.PENDING
        assert entry.next_retry_at is None
        assert entry.is_ready_for_retry is True

    def test_is_ready_for_retry_when_future(self):
        entry = _make_entry()
        entry.mark_failed("err")
        # next_retry_at is ~1s in the future
        assert entry.is_ready_for_retry is False

    def test_is_ready_for_retry_when_past(self):
        entry = _make_entry()
        entry.mark_failed("err")
        # Manually set to the past
        entry._next_retry_at = datetime.now(UTC) - timedelta(seconds=10)
        assert entry.is_ready_for_retry is True
