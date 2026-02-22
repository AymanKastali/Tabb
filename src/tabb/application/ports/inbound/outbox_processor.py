"""Inbound port — outbox processor interface."""

from abc import ABC, abstractmethod


class OutboxProcessor(ABC):
    """Processes pending outbox entries by dispatching to projectors."""

    @abstractmethod
    async def process_pending(self) -> int:
        """Process pending outbox entries.

        Returns the number of successfully processed entries.
        """
