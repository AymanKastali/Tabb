"""Tests for PlaceOrderCommand handler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from tabb.application.commands.place_order import PlaceOrderCommand, PlaceOrderHandler
from tabb.application.dto.order_dtos import OrderItemRequest
from tabb.domain.exceptions.business import EmptyOrderError, MenuItemNotAvailableError
from tabb.domain.models.menu_item import MenuItem, MenuItemId
from tabb.domain.models.value_objects import Money

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _menu_item(
    item_id: str = "m-1", name: str = "Burger", price: str = "9.99"
) -> MenuItem:
    return MenuItem.create(MenuItemId(item_id), name, Money(Decimal(price)))


def _item_request(
    menu_item_id: str = "m-1",
    name: str = "Burger",
    unit_price: str = "9.99",
    quantity: int = 1,
) -> OrderItemRequest:
    return OrderItemRequest(
        menu_item_id=menu_item_id,
        name=name,
        unit_price=Decimal(unit_price),
        quantity=quantity,
    )


def _command(
    order_id: str = "o-1",
    table_number: int = 5,
    items: list[OrderItemRequest] | None = None,
) -> PlaceOrderCommand:
    return PlaceOrderCommand(
        order_id=order_id,
        table_number=table_number,
        items=items if items is not None else [_item_request()],
    )


def _mock_uow(menu_item=None):
    uow = AsyncMock()
    uow.order_repository = AsyncMock()
    uow.menu_item_repository = AsyncMock()
    uow.menu_item_repository.find_by_id = AsyncMock(
        return_value=menu_item if menu_item is not None else _menu_item()
    )
    uow.outbox_repository = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPlaceOrderHandler:
    @pytest.fixture()
    def uow(self):
        return _mock_uow()

    @pytest.fixture()
    def id_generator(self) -> MagicMock:
        gen = MagicMock()
        gen.generate = MagicMock(return_value="generated-id")
        return gen

    @pytest.fixture()
    def handler(self, uow, id_generator: MagicMock) -> PlaceOrderHandler:
        return PlaceOrderHandler(uow, id_generator)

    async def test_places_order_successfully(self, handler, uow) -> None:
        await handler.handle(_command())

        uow.order_repository.save.assert_awaited_once()
        saved_order = uow.order_repository.save.call_args[0][0]
        assert str(saved_order.id) == "o-1"
        assert saved_order.table.value == 5
        assert len(saved_order.items) == 1
        uow.commit.assert_awaited_once()

    async def test_saves_outbox_entries(self, handler, uow) -> None:
        await handler.handle(_command())

        assert uow.outbox_repository.save.await_count >= 1

    async def test_verifies_menu_item_availability(self, id_generator) -> None:
        uow = _mock_uow(menu_item=None)
        uow.menu_item_repository.find_by_id = AsyncMock(return_value=None)
        handler = PlaceOrderHandler(uow, id_generator)

        with pytest.raises(MenuItemNotAvailableError):
            await handler.handle(_command())

        uow.order_repository.save.assert_not_awaited()

    async def test_sold_out_item_raises(self, id_generator) -> None:
        sold_out = _menu_item()
        sold_out.mark_sold_out()
        uow = _mock_uow(menu_item=sold_out)
        handler = PlaceOrderHandler(uow, id_generator)

        with pytest.raises(MenuItemNotAvailableError):
            await handler.handle(_command())

    async def test_empty_items_raises(self, handler) -> None:
        with pytest.raises(EmptyOrderError):
            await handler.handle(_command(items=[]))
