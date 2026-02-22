"""In-memory read model repository for orders."""

from __future__ import annotations

import copy

from tabb.application.ports.outbound.order_read_model_repository import (
    OrderReadModelRepository,
)
from tabb.application.read_models.order_read_model import OrderReadModel


class InMemoryOrderReadModelRepository(OrderReadModelRepository):
    """In-memory repository for order read models."""

    def __init__(self) -> None:
        self._store: dict[str, OrderReadModel] = {}

    async def find_by_id(self, order_id: str) -> OrderReadModel | None:
        rm = self._store.get(order_id)
        return copy.deepcopy(rm) if rm is not None else None

    async def save(self, read_model: OrderReadModel) -> None:
        self._store[read_model.order_id] = copy.deepcopy(read_model)

    async def delete(self, order_id: str) -> None:
        self._store.pop(order_id, None)
