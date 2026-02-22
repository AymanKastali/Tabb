"""Tests for GetOrderQuery handler."""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from tabb.application.dto.order_dtos import OrderResult
from tabb.application.exceptions import OrderNotFoundError
from tabb.application.queries.get_order import GetOrderHandler, GetOrderQuery
from tabb.application.read_models.order_read_model import (
    OrderItemReadModel,
    OrderReadModel,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _order_read_model() -> OrderReadModel:
    return OrderReadModel(
        order_id="o-1",
        table_number=5,
        status="open",
        items=[
            OrderItemReadModel(
                order_item_id="oi-1",
                menu_item_id="m-1",
                name="Burger",
                unit_price="9.99",
                quantity=2,
                status="pending",
                total_price="19.98",
            )
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetOrderHandler:
    @pytest.fixture()
    def read_repo(self):
        repo = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=_order_read_model())
        return repo

    @pytest.fixture()
    def handler(self, read_repo) -> GetOrderHandler:
        return GetOrderHandler(read_repo)

    async def test_returns_order_result(self, handler) -> None:
        result = await handler.handle(GetOrderQuery(order_id="o-1"))

        assert isinstance(result, OrderResult)
        assert result.order_id == "o-1"
        assert result.table_number == 5
        assert result.status == "open"
        assert len(result.items) == 1

        item = result.items[0]
        assert item.order_item_id == "oi-1"
        assert item.menu_item_id == "m-1"
        assert item.name == "Burger"
        assert item.unit_price == Decimal("9.99")
        assert item.quantity == 2
        assert item.status == "pending"
        assert item.total_price == Decimal("19.98")

    async def test_order_not_found_raises(self) -> None:
        read_repo = AsyncMock()
        read_repo.find_by_id = AsyncMock(return_value=None)
        handler = GetOrderHandler(read_repo)

        with pytest.raises(OrderNotFoundError):
            await handler.handle(GetOrderQuery(order_id="nonexistent"))
