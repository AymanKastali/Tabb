"""Outbound port — Unit of Work for atomic aggregate + outbox persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from tabb.application.ports.outbound.outbox_repository import OutboxRepository
from tabb.domain.ports.menu_item_repository import MenuItemRepository
from tabb.domain.ports.order_repository import OrderRepository


class UnitOfWork(ABC):
    """Ensures atomic persistence of aggregate state and outbox entries.

    Usage::

        async with uow:
            order = await uow.order_repository.find_by_id(order_id)
            order.cancel()
            await uow.order_repository.save(order)
            await uow.outbox_repository.save(outbox_entry)
            await uow.commit()
    """

    @property
    @abstractmethod
    def order_repository(self) -> OrderRepository:
        """Repository for the Order aggregate."""

    @property
    @abstractmethod
    def menu_item_repository(self) -> MenuItemRepository:
        """Repository for the MenuItem aggregate."""

    @property
    @abstractmethod
    def outbox_repository(self) -> OutboxRepository:
        """Repository for outbox entries."""

    @abstractmethod
    async def commit(self) -> None:
        """Atomically commit all changes."""

    @abstractmethod
    async def rollback(self) -> None:
        """Discard all pending changes."""

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork:
        """Enter the unit of work context."""

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the unit of work context, rolling back on error."""
