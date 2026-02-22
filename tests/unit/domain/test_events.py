"""Tests for domain events."""

import pytest

from tabb.domain.events.events import (
    DishMarkedReady,
    MenuItemAvailable,
    MenuItemCreated,
    MenuItemSoldOut,
    OrderCancelled,
    OrderCompleted,
    OrderItemAdded,
    OrderItemCancelled,
    OrderPlaced,
)
from tabb.domain.exceptions import RequiredFieldError


class TestDomainEventBase:
    def test_event_name(self) -> None:
        event = OrderPlaced(order_id="o-1", table_number=1)
        assert event.event_name == "OrderPlaced"

    def test_none_field_raises(self) -> None:
        with pytest.raises(RequiredFieldError):
            OrderPlaced(order_id=None, table_number=1)

    def test_immutable(self) -> None:
        event = OrderPlaced(order_id="o-1", table_number=1)
        with pytest.raises(AttributeError):
            event.order_id = "o-2"


class TestOrderEvents:
    def test_order_placed(self) -> None:
        event = OrderPlaced(order_id="o-1", table_number=5)
        assert event.order_id == "o-1"
        assert event.table_number == 5

    def test_order_item_added(self) -> None:
        event = OrderItemAdded(
            order_id="o-1",
            order_item_id="oi-1",
            menu_item_id="m-1",
            name="Burger",
            unit_price="9.99",
            quantity=2,
        )
        assert event.order_id == "o-1"
        assert event.order_item_id == "oi-1"
        assert event.menu_item_id == "m-1"
        assert event.name == "Burger"
        assert event.unit_price == "9.99"
        assert event.quantity == 2

    def test_order_item_cancelled(self) -> None:
        event = OrderItemCancelled(order_id="o-1", order_item_id="oi-1")
        assert event.order_id == "o-1"
        assert event.order_item_id == "oi-1"

    def test_dish_marked_ready(self) -> None:
        event = DishMarkedReady(order_id="o-1", order_item_id="oi-1")
        assert event.order_id == "o-1"

    def test_order_completed(self) -> None:
        event = OrderCompleted(order_id="o-1")
        assert event.order_id == "o-1"

    def test_order_cancelled(self) -> None:
        event = OrderCancelled(order_id="o-1")
        assert event.order_id == "o-1"


class TestMenuItemEvents:
    def test_menu_item_created(self) -> None:
        event = MenuItemCreated(menu_item_id="m-1", name="Burger", price="9.99")
        assert event.menu_item_id == "m-1"
        assert event.name == "Burger"
        assert event.price == "9.99"

    def test_menu_item_sold_out(self) -> None:
        event = MenuItemSoldOut(menu_item_id="m-1")
        assert event.menu_item_id == "m-1"

    def test_menu_item_available(self) -> None:
        event = MenuItemAvailable(menu_item_id="m-1")
        assert event.menu_item_id == "m-1"
