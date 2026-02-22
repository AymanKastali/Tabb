"""Tests for CancelOrderCommand handler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from tabb.application.commands.cancel_order import (
    CancelOrderCommand,
    CancelOrderHandler,
)
from tabb.application.exceptions import OrderNotFoundError
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


def _order() -> Order:
    order = Order.place(OrderId("o-1"), TableNumber(5))
    order.add_item(
        OrderItemId("oi-1"),
        MenuItemId("m-1"),
        "Burger",
        Money(Decimal("9.99")),
        Quantity(1),
    )
    return order


def _mock_uow(order=None):
    uow = AsyncMock()
    uow.order_repository = AsyncMock()
    uow.order_repository.find_by_id = AsyncMock(
        return_value=order if order is not None else _order()
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


class TestCancelOrderHandler:
    @pytest.fixture()
    def uow(self):
        return _mock_uow()

    @pytest.fixture()
    def handler(self, uow) -> CancelOrderHandler:
        return CancelOrderHandler(uow, _id_generator())

    async def test_cancels_order(self, handler, uow) -> None:
        await handler.handle(CancelOrderCommand(order_id="o-1"))

        uow.order_repository.save.assert_awaited_once()
        saved_order = uow.order_repository.save.call_args[0][0]
        assert saved_order.status == OrderStatus.CANCELLED
        uow.commit.assert_awaited_once()

    async def test_saves_outbox_entries(self, handler, uow) -> None:
        await handler.handle(CancelOrderCommand(order_id="o-1"))

        assert uow.outbox_repository.save.await_count >= 1

    async def test_order_not_found_raises(self) -> None:
        uow = _mock_uow()
        uow.order_repository.find_by_id = AsyncMock(return_value=None)
        handler = CancelOrderHandler(uow, _id_generator())

        with pytest.raises(OrderNotFoundError):
            await handler.handle(CancelOrderCommand(order_id="o-1"))
