"""Outbox entry model for the transactional outbox pattern."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime, timedelta
from enum import StrEnum, auto

from tabb.domain.events.base import DomainEvent


class OutboxEntryStatus(StrEnum):
    PENDING = auto()
    PROCESSED = auto()
    FAILED = auto()
    DEAD_LETTERED = auto()


@dataclass
class OutboxEntry:
    """Represents an event stored in the transactional outbox.

    Events are written atomically with aggregate changes, then
    projected to read models by a background processor.
    """

    _entry_id: str
    _event_type: str
    _event_data: dict[str, object]
    _aggregate_id: str
    _aggregate_type: str
    _occurred_at: datetime
    _status: OutboxEntryStatus = OutboxEntryStatus.PENDING
    _retry_count: int = 0
    _max_retries: int = 3
    _last_error: str | None = None
    _processed_at: datetime | None = None
    _next_retry_at: datetime | None = None
    _base_delay_seconds: int = 1

    def __post_init__(self) -> None:
        optional_fields = ("_last_error", "_processed_at", "_next_retry_at")
        for f in fields(self):
            val = getattr(self, f.name)
            if val is None and f.name not in optional_fields:
                raise ValueError(f"{f.name} is required")

    @property
    def entry_id(self) -> str:
        return self._entry_id

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def event_data(self) -> dict[str, object]:
        return dict(self._event_data)

    @property
    def aggregate_id(self) -> str:
        return self._aggregate_id

    @property
    def aggregate_type(self) -> str:
        return self._aggregate_type

    @property
    def occurred_at(self) -> datetime:
        return self._occurred_at

    @property
    def status(self) -> OutboxEntryStatus:
        return self._status

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def max_retries(self) -> int:
        return self._max_retries

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def processed_at(self) -> datetime | None:
        return self._processed_at

    @property
    def can_retry(self) -> bool:
        return self._retry_count < self._max_retries

    @property
    def next_retry_at(self) -> datetime | None:
        return self._next_retry_at

    @property
    def is_ready_for_retry(self) -> bool:
        """True if entry has no scheduled retry or the retry time has passed."""
        if self._next_retry_at is None:
            return True
        return datetime.now(UTC) >= self._next_retry_at

    @staticmethod
    def create(
        entry_id: str,
        event: DomainEvent,
        aggregate_id: str,
        aggregate_type: str,
    ) -> OutboxEntry:
        """Factory: create a new pending outbox entry from a domain event."""
        event_data: dict[str, object] = {
            f.name: getattr(event, f.name) for f in fields(event)
        }
        return OutboxEntry(
            _entry_id=entry_id,
            _event_type=event.event_name,
            _event_data=event_data,
            _aggregate_id=aggregate_id,
            _aggregate_type=aggregate_type,
            _occurred_at=datetime.now(UTC),
        )

    def mark_processed(self) -> None:
        """Mark this entry as successfully processed."""
        self._status = OutboxEntryStatus.PROCESSED
        self._processed_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        """Mark this entry as failed. Increments retry count.

        If max retries exceeded, entry becomes dead-lettered.
        Sets exponential backoff delay for retryable failures.
        """
        self._retry_count += 1
        self._last_error = error
        if not self.can_retry:
            self._status = OutboxEntryStatus.DEAD_LETTERED
            self._next_retry_at = None
        else:
            self._status = OutboxEntryStatus.FAILED
            delay = self._base_delay_seconds * (2 ** (self._retry_count - 1))
            self._next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)
