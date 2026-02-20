"""Repository port for the Order aggregate."""

from abc import ABC, abstractmethod

from tabb.domain.models.order import Order, OrderId


class OrderRepository(ABC):
    """Abstract repository for Order persistence."""

    @abstractmethod
    async def find_by_id(self, order_id: OrderId) -> Order | None:
        """Find an order by its identity. Returns None if not found."""

    @abstractmethod
    async def save(self, order: Order) -> None:
        """Persist an order (insert or update)."""
