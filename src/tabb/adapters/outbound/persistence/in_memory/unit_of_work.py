"""In-memory Unit of Work adapter with staged writes pattern."""

from __future__ import annotations

from types import TracebackType

from tabb.adapters.outbound.persistence.in_memory.menu_item_repository import (
    InMemoryMenuItemRepository,
)
from tabb.adapters.outbound.persistence.in_memory.order_repository import (
    InMemoryOrderRepository,
)
from tabb.adapters.outbound.persistence.in_memory.outbox_repository import (
    InMemoryOutboxRepository,
)
from tabb.application.outbox import OutboxEntry
from tabb.application.ports.outbound.outbox_repository import OutboxRepository
from tabb.application.ports.outbound.unit_of_work import UnitOfWork
from tabb.domain.models.menu_item import MenuItem
from tabb.domain.models.order import Order
from tabb.domain.ports.menu_item_repository import MenuItemRepository
from tabb.domain.ports.order_repository import OrderRepository


class InMemoryUnitOfWork(UnitOfWork):
    """In-memory UoW using staged writes pattern.

    Each ``async with uow`` creates fresh staging-area repositories.
    ``commit()`` flushes all staged changes to the shared stores.
    ``rollback()`` discards staged changes.
    """

    def __init__(
        self,
        order_store: dict[str, Order],
        menu_item_store: dict[str, MenuItem],
        outbox_store: list[OutboxEntry],
    ) -> None:
        self._order_store = order_store
        self._menu_item_store = menu_item_store
        self._outbox_store = outbox_store

        self._order_repo: InMemoryOrderRepository | None = None
        self._menu_item_repo: InMemoryMenuItemRepository | None = None
        self._outbox_repo: InMemoryOutboxRepository | None = None

    @property
    def order_repository(self) -> OrderRepository:
        if self._order_repo is None:
            raise RuntimeError("UnitOfWork not entered")
        return self._order_repo

    @property
    def menu_item_repository(self) -> MenuItemRepository:
        if self._menu_item_repo is None:
            raise RuntimeError("UnitOfWork not entered")
        return self._menu_item_repo

    @property
    def outbox_repository(self) -> OutboxRepository:
        if self._outbox_repo is None:
            raise RuntimeError("UnitOfWork not entered")
        return self._outbox_repo

    async def commit(self) -> None:
        if self._order_repo is not None:
            self._order_repo.flush()
        if self._menu_item_repo is not None:
            self._menu_item_repo.flush()
        if self._outbox_repo is not None:
            self._outbox_repo.flush()

    async def rollback(self) -> None:
        if self._order_repo is not None:
            self._order_repo.discard()
        if self._menu_item_repo is not None:
            self._menu_item_repo.discard()
        if self._outbox_repo is not None:
            self._outbox_repo.discard()

    async def __aenter__(self) -> InMemoryUnitOfWork:
        self._order_repo = InMemoryOrderRepository(self._order_store)
        self._menu_item_repo = InMemoryMenuItemRepository(self._menu_item_store)
        self._outbox_repo = InMemoryOutboxRepository(self._outbox_store)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        self._order_repo = None
        self._menu_item_repo = None
        self._outbox_repo = None
