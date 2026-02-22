"""Port for generating unique identifiers."""

from abc import ABC, abstractmethod


class IdGenerator(ABC):
    """Abstract port for generating unique string identifiers."""

    @abstractmethod
    def generate(self) -> str:
        """Generate a new unique identifier."""
