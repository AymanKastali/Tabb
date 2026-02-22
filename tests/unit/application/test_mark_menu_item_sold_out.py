"""Tests for MarkMenuItemSoldOutCommand handler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from tabb.application.commands.mark_menu_item_sold_out import (
    MarkMenuItemSoldOutCommand,
    MarkMenuItemSoldOutHandler,
)
from tabb.application.exceptions import MenuItemNotFoundError
from tabb.domain.models.menu_item import MenuItem, MenuItemId
from tabb.domain.models.value_objects import Money

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _menu_item() -> MenuItem:
    return MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))


def _mock_uow(menu_item=None):
    uow = AsyncMock()
    uow.menu_item_repository = AsyncMock()
    uow.menu_item_repository.find_by_id = AsyncMock(
        return_value=menu_item if menu_item is not None else _menu_item()
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


class TestMarkMenuItemSoldOutHandler:
    @pytest.fixture()
    def uow(self):
        return _mock_uow()

    @pytest.fixture()
    def handler(self, uow) -> MarkMenuItemSoldOutHandler:
        return MarkMenuItemSoldOutHandler(uow, _id_generator())

    async def test_marks_sold_out(self, handler, uow) -> None:
        await handler.handle(MarkMenuItemSoldOutCommand(menu_item_id="m-1"))

        uow.menu_item_repository.save.assert_awaited_once()
        saved = uow.menu_item_repository.save.call_args[0][0]
        assert saved.available is False
        uow.commit.assert_awaited_once()

    async def test_saves_outbox_entries(self, handler, uow) -> None:
        await handler.handle(MarkMenuItemSoldOutCommand(menu_item_id="m-1"))

        assert uow.outbox_repository.save.await_count >= 1

    async def test_not_found_raises(self) -> None:
        uow = _mock_uow()
        uow.menu_item_repository.find_by_id = AsyncMock(return_value=None)
        handler = MarkMenuItemSoldOutHandler(uow, _id_generator())

        with pytest.raises(MenuItemNotFoundError):
            await handler.handle(MarkMenuItemSoldOutCommand(menu_item_id="m-1"))
