"""Tests for CompleteOrderCommand handler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from tabb.application.commands.complete_order import (
    CompleteOrderCommand,
    CompleteOrderHandler,
)
from tabb.application.exceptions import OrderNotFoundError
from tabb.domain.exceptions.business import OrderNotFullyReadyError
from tabb.domain.models.menu_item import MenuItemId
from tabb.domain.models.order import (
    Order,
    OrderId,
    OrderItemId,
    OrderStatus,
)
from tabb.domain.models.value_objects import Money, Quantity, TableNumber

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _order(ready: bool = False) -> Order:
    order = Order.place(OrderId("o-1"), TableNumber(5))
    order.add_item(
        OrderItemId("oi-1"),
        MenuItemId("m-1"),
        "Burger",
        Money(Decimal("9.99")),
        Quantity(1),
    )
    if ready:
        order.mark_item_ready(OrderItemId("oi-1"))
    return order


def _mock_uow(order=None):
    uow = AsyncMock()
    uow.order_repository = AsyncMock()
    uow.order_repository.find_by_id = AsyncMock(
        return_value=order if order is not None else _order(ready=True)
    )
    uow.outbox_repository = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


def _id_generator():
    gen = MagicMock()
    gen.generate = MagicMock(return_value="generated-id")
    return gen


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCompleteOrderHandler:
    @pytest.fixture()
    def uow(self):
        return _mock_uow()

    @pytest.fixture()
    def handler(self, uow) -> CompleteOrderHandler:
        return CompleteOrderHandler(uow, _id_generator())

    async def test_completes_order(self, handler, uow) -> None:
        await handler.handle(CompleteOrderCommand(order_id="o-1"))

        uow.order_repository.save.assert_awaited_once()
        saved_order = uow.order_repository.save.call_args[0][0]
        assert saved_order.status == OrderStatus.COMPLETED
        uow.commit.assert_awaited_once()

    async def test_saves_outbox_entries(self, handler, uow) -> None:
        await handler.handle(CompleteOrderCommand(order_id="o-1"))

        assert uow.outbox_repository.save.await_count >= 1

    async def test_order_not_found_raises(self) -> None:
        uow = _mock_uow()
        uow.order_repository.find_by_id = AsyncMock(return_value=None)
        handler = CompleteOrderHandler(uow, _id_generator())

        with pytest.raises(OrderNotFoundError):
            await handler.handle(CompleteOrderCommand(order_id="o-1"))

    async def test_items_not_ready_raises(self) -> None:
        uow = _mock_uow(order=_order(ready=False))
        handler = CompleteOrderHandler(uow, _id_generator())

        with pytest.raises(OrderNotFullyReadyError):
            await handler.handle(CompleteOrderCommand(order_id="o-1"))
