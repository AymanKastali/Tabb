"""Inbound port — CQRS command abstractions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, kw_only=True)
class Command:
    """Base class for all commands. Commands are immutable data carriers."""


class CommandHandler(ABC):
    """Handles a single command type."""

    @abstractmethod
    async def handle(self, command: Command) -> Any:
        """Execute the command."""


class CommandBus(ABC):
    """Dispatches commands to their registered handlers."""

    @abstractmethod
    async def dispatch(self, command: Command) -> Any:
        """Route a command to the appropriate handler and execute it."""
