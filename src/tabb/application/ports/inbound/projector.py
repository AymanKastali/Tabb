"""Inbound port — projector interface for event-driven read model updates."""

from abc import ABC, abstractmethod


class Projector(ABC):
    """Projects domain events into read models.

    Each projector handles specific event types and updates the
    corresponding read model repository.
    """

    @abstractmethod
    def handles(self) -> list[str]:
        """Return the event type names this projector handles."""

    @abstractmethod
    async def project(self, event_type: str, event_data: dict[str, object]) -> None:
        """Project an event into the read model."""
