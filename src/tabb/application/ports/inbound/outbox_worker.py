"""Inbound port — outbox background worker interface."""

from abc import ABC, abstractmethod


class OutboxWorker(ABC):
    """Drives repeated outbox processing in the background.

    Implementations decide the scheduling mechanism (asyncio, threading, etc.).
    """

    @abstractmethod
    async def start(self) -> None:
        """Start the background processing loop."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the background processing loop and clean up resources."""
