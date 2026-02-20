"""Tests for OrderDomainService."""

from decimal import Decimal

import pytest

from tabb.domain.exceptions.business import MenuItemNotAvailableError
from tabb.domain.models.menu_item import MenuItem, MenuItemId
from tabb.domain.models.value_objects import Money
from tabb.domain.services.order_service import OrderDomainService


class TestVerifyItemsAvailable:
    def test_all_available_passes(self) -> None:
        items = [
            MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99"))),
            MenuItem.create(MenuItemId("m-2"), "Fries", Money(Decimal("4.99"))),
        ]
        # Should not raise
        OrderDomainService.verify_items_available(
            [MenuItemId("m-1"), MenuItemId("m-2")], items
        )

    def test_sold_out_item_raises(self) -> None:
        burger = MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))
        burger.mark_sold_out()

        with pytest.raises(MenuItemNotAvailableError) as exc_info:
            OrderDomainService.verify_items_available([MenuItemId("m-1")], [burger])

        assert "m-1" in exc_info.value.menu_item_ids

    def test_missing_item_raises(self) -> None:
        available = [
            MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99"))),
        ]
        with pytest.raises(MenuItemNotAvailableError) as exc_info:
            OrderDomainService.verify_items_available(
                [MenuItemId("m-1"), MenuItemId("m-999")], available
            )

        assert "m-999" in exc_info.value.menu_item_ids

    def test_mix_of_available_and_sold_out(self) -> None:
        burger = MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))
        fries = MenuItem.create(MenuItemId("m-2"), "Fries", Money(Decimal("4.99")))
        fries.mark_sold_out()

        with pytest.raises(MenuItemNotAvailableError) as exc_info:
            OrderDomainService.verify_items_available(
                [MenuItemId("m-1"), MenuItemId("m-2")], [burger, fries]
            )

        assert "m-2" in exc_info.value.menu_item_ids
        assert "m-1" not in exc_info.value.menu_item_ids

    def test_empty_request_passes(self) -> None:
        OrderDomainService.verify_items_available([], [])
