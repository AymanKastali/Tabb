"""Tests for GetAvailableMenuItemsQuery handler."""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from tabb.application.dto.menu_item_dtos import MenuItemResult
from tabb.application.queries.get_available_menu_items import (
    GetAvailableMenuItemsHandler,
    GetAvailableMenuItemsQuery,
)
from tabb.application.read_models.menu_item_read_model import MenuItemReadModel

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetAvailableMenuItemsHandler:
    @pytest.fixture()
    def read_repo(self):
        repo = AsyncMock()
        repo.find_all_available = AsyncMock(
            return_value=[
                MenuItemReadModel(
                    menu_item_id="m-1", name="Burger", price="9.99", available=True
                ),
                MenuItemReadModel(
                    menu_item_id="m-2", name="Fries", price="4.99", available=True
                ),
            ]
        )
        return repo

    @pytest.fixture()
    def handler(self, read_repo) -> GetAvailableMenuItemsHandler:
        return GetAvailableMenuItemsHandler(read_repo)

    async def test_returns_available_items(self, handler) -> None:
        result = await handler.handle(GetAvailableMenuItemsQuery())

        assert len(result) == 2
        assert all(isinstance(r, MenuItemResult) for r in result)
        assert result[0].menu_item_id == "m-1"
        assert result[0].name == "Burger"
        assert result[0].price == Decimal("9.99")
        assert result[0].available is True
        assert result[1].menu_item_id == "m-2"

    async def test_returns_empty_list_when_none_available(self) -> None:
        read_repo = AsyncMock()
        read_repo.find_all_available = AsyncMock(return_value=[])
        handler = GetAvailableMenuItemsHandler(read_repo)

        result = await handler.handle(GetAvailableMenuItemsQuery())

        assert result == []
