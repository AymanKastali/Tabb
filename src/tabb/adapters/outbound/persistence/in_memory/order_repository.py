"""In-memory Order repository adapter with staged writes for UoW."""

from __future__ import annotations

import copy

from tabb.domain.models.order import Order, OrderId
from tabb.domain.ports.order_repository import OrderRepository


class InMemoryOrderRepository(OrderRepository):
    """In-memory write-side repository for Order aggregates.

    Supports staged writes: saves go to a staging area, which is
    applied to the committed store on UoW commit, or discarded on rollback.
    Reads check staging first (read-your-writes), then committed store.
    """

    def __init__(self, store: dict[str, Order]) -> None:
        self._store = store
        self._staging: dict[str, Order] = {}

    async def find_by_id(self, order_id: OrderId) -> Order | None:
        key = str(order_id)
        if key in self._staging:
            return copy.deepcopy(self._staging[key])
        if key in self._store:
            return copy.deepcopy(self._store[key])
        return None

    async def save(self, order: Order) -> None:
        self._staging[str(order.id)] = copy.deepcopy(order)

    def flush(self) -> None:
        """Apply staged writes to the committed store."""
        self._store.update(self._staging)
        self._staging.clear()

    def discard(self) -> None:
        """Discard staged writes."""
        self._staging.clear()
