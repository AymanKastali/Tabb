"""Tests for Order aggregate and OrderItem entity."""

from decimal import Decimal

import pytest

from tabb.domain.events.events import (
    DishMarkedReady,
    OrderCancelled,
    OrderCompleted,
    OrderItemAdded,
    OrderItemCancelled,
    OrderPlaced,
)
from tabb.domain.exceptions.business import (
    InvalidOrderItemStateError,
    OrderItemNotFoundError,
    OrderNotFullyReadyError,
    OrderNotOpenError,
)
from tabb.domain.exceptions.validation import InvalidFieldTypeError, RequiredFieldError
from tabb.domain.models.menu_item import MenuItemId
from tabb.domain.models.order import (
    Order,
    OrderId,
    OrderItem,
    OrderItemId,
    OrderItemStatus,
    OrderStatus,
)
from tabb.domain.models.value_objects import Money, Quantity, TableNumber


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _money(amount: str) -> Money:
    return Money(Decimal(amount))


def _item(
    item_id: str = "oi-1",
    menu_item_id: str = "m-1",
    name: str = "Burger",
    price: str = "9.99",
    qty: int = 1,
) -> OrderItem:
    return OrderItem(
        _id=OrderItemId(item_id),
        _menu_item_id=menu_item_id,
        _name=name,
        _unit_price=_money(price),
        _quantity=Quantity(qty),
    )


def _place_and_add(
    order_id: str = "o-1",
    table: int = 5,
    items: list[tuple[str, str, str, str, int]] | None = None,
) -> Order:
    """Place an order and add items via add_item()."""
    order = Order.place(OrderId(order_id), TableNumber(table))
    for item_id, menu_id, name, price, qty in (
        items if items is not None else [("oi-1", "m-1", "Burger", "9.99", 1)]
    ):
        order.add_item(
            OrderItemId(item_id),
            MenuItemId(menu_id),
            name,
            _money(price),
            Quantity(qty),
        )
    return order


# ---------------------------------------------------------------------------
# OrderItem Validation
# ---------------------------------------------------------------------------


class TestOrderItemValidation:
    def test_valid_order_item(self) -> None:
        oi = _item()
        assert oi.menu_item_id == "m-1"
        assert oi.name == "Burger"
        assert oi.unit_price == _money("9.99")
        assert oi.quantity == Quantity(1)
        assert oi.status == OrderItemStatus.PENDING

    def test_blank_menu_item_id_raises(self) -> None:
        with pytest.raises(RequiredFieldError):
            _item(menu_item_id="  ")

    def test_blank_name_raises(self) -> None:
        with pytest.raises(RequiredFieldError):
            _item(name="")

    def test_wrong_id_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            OrderItem(
                _id="bad",
                _menu_item_id="m-1",
                _name="X",
                _unit_price=_money("1"),
                _quantity=Quantity(1),
            )

    def test_wrong_unit_price_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            OrderItem(
                _id=OrderItemId("oi-1"),
                _menu_item_id="m-1",
                _name="X",
                _unit_price="9.99",
                _quantity=Quantity(1),
            )

    def test_wrong_quantity_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            OrderItem(
                _id=OrderItemId("oi-1"),
                _menu_item_id="m-1",
                _name="X",
                _unit_price=_money("1"),
                _quantity=3,
            )

    def test_total_price(self) -> None:
        oi = _item(price="10.00", qty=3)
        assert oi.total_price == _money("30.00")


# ---------------------------------------------------------------------------
# OrderItem State Transitions
# ---------------------------------------------------------------------------


class TestOrderItemStateMachine:
    def test_mark_preparing_from_pending(self) -> None:
        oi = _item()
        oi.mark_preparing()
        assert oi.status == OrderItemStatus.PREPARING

    def test_mark_preparing_from_non_pending_raises(self) -> None:
        oi = _item()
        oi.mark_preparing()
        with pytest.raises(InvalidOrderItemStateError):
            oi.mark_preparing()

    def test_mark_ready_from_pending(self) -> None:
        oi = _item()
        oi.mark_ready()
        assert oi.status == OrderItemStatus.READY

    def test_mark_ready_from_preparing(self) -> None:
        oi = _item()
        oi.mark_preparing()
        oi.mark_ready()
        assert oi.status == OrderItemStatus.READY

    def test_mark_ready_from_ready_raises(self) -> None:
        oi = _item()
        oi.mark_ready()
        with pytest.raises(InvalidOrderItemStateError):
            oi.mark_ready()

    def test_mark_ready_from_cancelled_raises(self) -> None:
        oi = _item()
        oi.cancel()
        with pytest.raises(InvalidOrderItemStateError):
            oi.mark_ready()

    def test_cancel_from_pending(self) -> None:
        oi = _item()
        oi.cancel()
        assert oi.status == OrderItemStatus.CANCELLED

    def test_cancel_from_preparing(self) -> None:
        oi = _item()
        oi.mark_preparing()
        oi.cancel()
        assert oi.status == OrderItemStatus.CANCELLED

    def test_cancel_from_ready_raises(self) -> None:
        oi = _item()
        oi.mark_ready()
        with pytest.raises(InvalidOrderItemStateError):
            oi.cancel()

    def test_cancel_idempotent(self) -> None:
        oi = _item()
        oi.cancel()
        oi.cancel()  # should not raise
        assert oi.status == OrderItemStatus.CANCELLED


# ---------------------------------------------------------------------------
# Order Validation
# ---------------------------------------------------------------------------


class TestOrderValidation:
    def test_wrong_id_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            Order(
                _id="bad",
                _table=TableNumber(1),
                _items=[_item()],
            )

    def test_wrong_table_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            Order(
                _id=OrderId("o-1"),
                _table=5,
                _items=[_item()],
            )

    def test_wrong_items_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            Order(
                _id=OrderId("o-1"),
                _table=TableNumber(1),
                _items="not a list",
            )

    def test_non_order_item_in_list_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            Order(
                _id=OrderId("o-1"),
                _table=TableNumber(1),
                _items=["not an item"],
            )


# ---------------------------------------------------------------------------
# Order.place() Factory
# ---------------------------------------------------------------------------


class TestOrderPlace:
    def test_place_creates_open_order(self) -> None:
        order = Order.place(OrderId("o-1"), TableNumber(5))
        assert order.status == OrderStatus.OPEN
        assert order.table == TableNumber(5)
        assert len(order.items) == 0

    def test_place_records_order_placed_event(self) -> None:
        order = Order.place(OrderId("o-1"), TableNumber(5))
        events = order.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderPlaced)
        assert events[0].order_id == "o-1"
        assert events[0].table_number == 5


# ---------------------------------------------------------------------------
# Order.add_item()
# ---------------------------------------------------------------------------


class TestOrderAddItem:
    def test_add_item(self) -> None:
        order = Order.place(OrderId("o-1"), TableNumber(5))
        order.collect_events()

        order.add_item(
            OrderItemId("oi-1"),
            MenuItemId("m-1"),
            "Burger",
            _money("9.99"),
            Quantity(1),
        )

        assert len(order.items) == 1
        events = order.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderItemAdded)
        assert events[0].order_item_id == "oi-1"
        assert events[0].menu_item_id == "m-1"
        assert events[0].name == "Burger"
        assert events[0].unit_price == "9.99"

    def test_add_item_to_completed_order_raises(self) -> None:
        order = _place_and_add()
        order.mark_item_ready(OrderItemId("oi-1"))
        order.complete()
        with pytest.raises(OrderNotOpenError):
            order.add_item(
                OrderItemId("oi-2"),
                MenuItemId("m-2"),
                "Fries",
                _money("4.99"),
                Quantity(1),
            )


# ---------------------------------------------------------------------------
# Order.cancel_item()
# ---------------------------------------------------------------------------


class TestOrderCancelItem:
    def test_cancel_item(self) -> None:
        order = _place_and_add()
        order.collect_events()

        order.cancel_item(OrderItemId("oi-1"))

        events = order.collect_events()
        assert any(isinstance(e, OrderItemCancelled) for e in events)

    def test_cancel_item_not_found_raises(self) -> None:
        order = _place_and_add()
        with pytest.raises(OrderItemNotFoundError):
            order.cancel_item(OrderItemId("nonexistent"))

    def test_cancel_all_items_auto_cancels_order(self) -> None:
        order = _place_and_add()
        order.collect_events()

        order.cancel_item(OrderItemId("oi-1"))

        assert order.status == OrderStatus.CANCELLED
        events = order.collect_events()
        event_types = [type(e) for e in events]
        assert OrderItemCancelled in event_types
        assert OrderCancelled in event_types

    def test_cancel_item_on_cancelled_order_raises(self) -> None:
        order = _place_and_add()
        order.cancel()
        with pytest.raises(OrderNotOpenError):
            order.cancel_item(OrderItemId("oi-1"))


# ---------------------------------------------------------------------------
# Order.mark_item_ready()
# ---------------------------------------------------------------------------


class TestOrderMarkItemReady:
    def test_mark_item_ready(self) -> None:
        order = _place_and_add()
        order.collect_events()

        order.mark_item_ready(OrderItemId("oi-1"))

        events = order.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], DishMarkedReady)
        assert events[0].order_item_id == "oi-1"

    def test_mark_item_ready_not_found_raises(self) -> None:
        order = _place_and_add()
        with pytest.raises(OrderItemNotFoundError):
            order.mark_item_ready(OrderItemId("nonexistent"))


# ---------------------------------------------------------------------------
# Order.complete()
# ---------------------------------------------------------------------------


class TestOrderComplete:
    def test_complete_when_all_ready(self) -> None:
        order = _place_and_add()
        order.mark_item_ready(OrderItemId("oi-1"))
        order.collect_events()

        order.complete()

        assert order.status == OrderStatus.COMPLETED
        events = order.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderCompleted)

    def test_complete_with_pending_items_raises(self) -> None:
        order = _place_and_add()
        with pytest.raises(OrderNotFullyReadyError):
            order.complete()

    def test_complete_with_mix_of_ready_and_cancelled(self) -> None:
        order = _place_and_add(
            items=[
                ("oi-1", "m-1", "Burger", "9.99", 1),
                ("oi-2", "m-2", "Fries", "4.99", 1),
            ]
        )

        order.cancel_item(OrderItemId("oi-1"))
        order.mark_item_ready(OrderItemId("oi-2"))
        order.collect_events()

        order.complete()
        assert order.status == OrderStatus.COMPLETED

    def test_complete_already_completed_raises(self) -> None:
        order = _place_and_add()
        order.mark_item_ready(OrderItemId("oi-1"))
        order.complete()
        with pytest.raises(OrderNotOpenError):
            order.complete()


# ---------------------------------------------------------------------------
# Order.cancel()
# ---------------------------------------------------------------------------


class TestOrderCancel:
    def test_cancel_order(self) -> None:
        order = _place_and_add()
        order.collect_events()

        order.cancel()

        assert order.status == OrderStatus.CANCELLED
        events = order.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderCancelled)

    def test_cancel_sets_non_ready_items_to_cancelled(self) -> None:
        order = _place_and_add(
            items=[
                ("oi-1", "m-1", "Burger", "9.99", 1),
                ("oi-2", "m-2", "Fries", "4.99", 1),
            ]
        )
        order.mark_item_ready(OrderItemId("oi-1"))

        order.cancel()

        # oi-1 was READY, should stay READY
        # oi-2 was PENDING, should become CANCELLED
        oi1 = next(i for i in order.items if i.id == OrderItemId("oi-1"))
        oi2 = next(i for i in order.items if i.id == OrderItemId("oi-2"))
        assert oi1.status == OrderItemStatus.READY
        assert oi2.status == OrderItemStatus.CANCELLED

    def test_cancel_already_cancelled_raises(self) -> None:
        order = _place_and_add()
        order.cancel()
        with pytest.raises(OrderNotOpenError):
            order.cancel()


# ---------------------------------------------------------------------------
# Order.active_items / Order.items
# ---------------------------------------------------------------------------


class TestOrderQueries:
    def test_active_items_excludes_cancelled(self) -> None:
        order = _place_and_add(
            items=[
                ("oi-1", "m-1", "Burger", "9.99", 1),
                ("oi-2", "m-2", "Fries", "4.99", 1),
            ]
        )
        order.cancel_item(OrderItemId("oi-1"))

        assert len(order.active_items) == 1
        assert order.active_items[0].id == OrderItemId("oi-2")

    def test_items_returns_defensive_copy(self) -> None:
        order = _place_and_add()
        items = order.items
        items.append(_item(item_id="oi-2"))
        assert len(order.items) == 1
