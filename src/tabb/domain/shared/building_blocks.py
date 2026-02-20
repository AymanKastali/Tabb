"""Domain building blocks for the shared kernel."""

from dataclasses import dataclass, field

from tabb.domain.events.base import DomainEvent
from tabb.domain.exceptions import RequiredFieldError


@dataclass(frozen=True, slots=True)
class Id[T]:
    """Generic identity value object.

    Wraps a raw value (UUID, int, str, etc.) and enforces non-null,
    non-blank validation on construction.
    """

    value: T

    def __post_init__(self) -> None:
        if self.value is None:
            raise RequiredFieldError(type(self).__name__, "value")

        if isinstance(self.value, str) and not self.value.strip():
            raise RequiredFieldError(type(self).__name__, "value")

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))

    def __bool__(self) -> bool:
        return bool(self.value)


@dataclass
class Entity[IdT]:
    """Base class for all domain entities.

    Entities are objects with a unique identity that persists over time.
    Equality is based on identity, not structural equality.
    """

    _id: IdT

    @property
    def id(self) -> IdT:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)


@dataclass
class AggregateRoot[IdT](Entity[IdT]):
    """Base class for aggregate roots.

    An aggregate root is the entry point to an aggregate — a cluster of
    entities and value objects treated as a single consistency boundary.
    It also collects domain events for later dispatch.
    """

    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def _record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        events = self._events.copy()
        self._events.clear()
        return events
