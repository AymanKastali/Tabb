"""Base domain event for tabb."""

from dataclasses import dataclass, fields

from tabb.domain.exceptions import RequiredFieldError


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events.

    Events are immutable records of something meaningful that happened
    in the domain. All fields are required and validated on construction.
    """

    def __post_init__(self) -> None:
        for f in fields(self):
            if getattr(self, f.name) is None:
                raise RequiredFieldError(type(self).__name__, f.name)

    @property
    def event_name(self) -> str:
        return type(self).__name__
