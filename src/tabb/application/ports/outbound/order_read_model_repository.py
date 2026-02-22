"""Outbound port — read model repository for orders."""

from __future__ import annotations

from abc import ABC, abstractmethod

from tabb.application.read_models.order_read_model import OrderReadModel


class OrderReadModelRepository(ABC):
    """Abstract repository for the order read model."""

    @abstractmethod
    async def find_by_id(self, order_id: str) -> OrderReadModel | None:
        """Find an order read model by its ID."""

    @abstractmethod
    async def save(self, read_model: OrderReadModel) -> None:
        """Persist an order read model (insert or update)."""

    @abstractmethod
    async def delete(self, order_id: str) -> None:
        """Delete an order read model."""
