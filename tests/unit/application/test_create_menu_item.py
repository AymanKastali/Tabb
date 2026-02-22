"""Tests for CreateMenuItemCommand handler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from tabb.application.commands.create_menu_item import (
    CreateMenuItemCommand,
    CreateMenuItemHandler,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_uow():
    uow = AsyncMock()
    uow.menu_item_repository = AsyncMock()
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


class TestCreateMenuItemHandler:
    @pytest.fixture()
    def uow(self):
        return _mock_uow()

    @pytest.fixture()
    def handler(self, uow) -> CreateMenuItemHandler:
        return CreateMenuItemHandler(uow, _id_generator())

    async def test_creates_menu_item(self, handler, uow) -> None:
        await handler.handle(
            CreateMenuItemCommand(
                menu_item_id="m-1",
                name="Burger",
                price=Decimal("9.99"),
            )
        )

        uow.menu_item_repository.save.assert_awaited_once()
        saved = uow.menu_item_repository.save.call_args[0][0]
        assert str(saved.id) == "m-1"
        assert saved.name == "Burger"
        assert saved.price.amount == Decimal("9.99")
        assert saved.available is True
        uow.commit.assert_awaited_once()

    async def test_saves_outbox_entries(self, handler, uow) -> None:
        await handler.handle(
            CreateMenuItemCommand(
                menu_item_id="m-1",
                name="Burger",
                price=Decimal("9.99"),
            )
        )

        assert uow.outbox_repository.save.await_count >= 1
