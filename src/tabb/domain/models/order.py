"""Order aggregate — manages the ordering lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto

from tabb.domain.events.events import (
    DishMarkedReady,
    OrderCancelled,
    OrderCompleted,
    OrderItemAdded,
    OrderItemCancelled,
    OrderPlaced,
)
from tabb.domain.exceptions.business import (
    EmptyOrderError,
    InvalidOrderItemStateError,
    OrderItemNotFoundError,
    OrderNotFullyReadyError,
    OrderNotOpenError,
)
from tabb.domain.exceptions.validation import InvalidFieldTypeError, RequiredFieldError
from tabb.domain.models.value_objects import Money, Quantity, TableNumber
from tabb.domain.shared.building_blocks import AggregateRoot, Entity, Id

# ---------------------------------------------------------------------------
# Identity Value Objects
# ---------------------------------------------------------------------------


class OrderId(Id[str]):
    """Identity for an order."""


class OrderItemId(Id[str]):
    """Identity for an order item."""


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OrderStatus(StrEnum):
    OPEN = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class OrderItemStatus(StrEnum):
    PENDING = auto()
    PREPARING = auto()
    READY = auto()
    CANCELLED = auto()


# ---------------------------------------------------------------------------
# OrderItem Entity
# ---------------------------------------------------------------------------


@dataclass
class OrderItem(Entity[OrderItemId]):
    """An item within an order. Tracks its preparation status."""

    _menu_item_id: str
    _name: str
    _unit_price: Money
    _quantity: Quantity
    _status: OrderItemStatus = OrderItemStatus.PENDING

    def __post_init__(self) -> None:
        cls_name = type(self).__name__

        if not isinstance(self._id, OrderItemId):
            raise InvalidFieldTypeError(cls_name, "id", "OrderItemId")
        if not isinstance(self._menu_item_id, str) or not self._menu_item_id.strip():
            raise RequiredFieldError(cls_name, "menu_item_id")
        if not isinstance(self._name, str) or not self._name.strip():
            raise RequiredFieldError(cls_name, "name")
        if not isinstance(self._unit_price, Money):
            raise InvalidFieldTypeError(cls_name, "unit_price", "Money")
        if not isinstance(self._quantity, Quantity):
            raise InvalidFieldTypeError(cls_name, "quantity", "Quantity")
        if not isinstance(self._status, OrderItemStatus):
            raise InvalidFieldTypeError(cls_name, "status", "OrderItemStatus")

    @property
    def menu_item_id(self) -> str:
        return self._menu_item_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def unit_price(self) -> Money:
        return self._unit_price

    @property
    def quantity(self) -> Quantity:
        return self._quantity

    @property
    def status(self) -> OrderItemStatus:
        return self._status

    @property
    def total_price(self) -> Money:
        return self._unit_price * self._quantity.value

    def mark_preparing(self) -> None:
        if self._status != OrderItemStatus.PENDING:
            raise InvalidOrderItemStateError(
                str(self.id), self._status.value, "mark as preparing"
            )
        self._status = OrderItemStatus.PREPARING

    def mark_ready(self) -> None:
        if self._status not in (OrderItemStatus.PENDING, OrderItemStatus.PREPARING):
            raise InvalidOrderItemStateError(
                str(self.id), self._status.value, "mark as ready"
            )
        self._status = OrderItemStatus.READY

    def cancel(self) -> None:
        if self._status == OrderItemStatus.READY:
            raise InvalidOrderItemStateError(
                str(self.id), self._status.value, "cancel"
            )
        if self._status == OrderItemStatus.CANCELLED:
            return
        self._status = OrderItemStatus.CANCELLED


# ---------------------------------------------------------------------------
# Order Aggregate Root
# ---------------------------------------------------------------------------


@dataclass
class Order(AggregateRoot[OrderId]):
    """Aggregate root for a customer order.

    Lifecycle: OPEN -> COMPLETED | CANCELLED
    Items follow: PENDING -> PREPARING -> READY (or CANCELLED at any non-READY point).

    Must be created via the ``place`` factory method.
    """

    _table: TableNumber
    _items: list[OrderItem] = field(default_factory=list)
    _status: OrderStatus = OrderStatus.OPEN

    def __post_init__(self) -> None:
        cls_name = type(self).__name__

        if not isinstance(self._id, OrderId):
            raise InvalidFieldTypeError(cls_name, "id", "OrderId")
        if not isinstance(self._table, TableNumber):
            raise InvalidFieldTypeError(cls_name, "table", "TableNumber")
        if not isinstance(self._items, list):
            raise InvalidFieldTypeError(cls_name, "items", "list[OrderItem]")
        for i, item in enumerate(self._items):
            if not isinstance(item, OrderItem):
                raise InvalidFieldTypeError(cls_name, f"items[{i}]", "OrderItem")
        if not isinstance(self._status, OrderStatus):
            raise InvalidFieldTypeError(cls_name, "status", "OrderStatus")

    @property
    def table(self) -> TableNumber:
        return self._table

    @property
    def items(self) -> list[OrderItem]:
        return list(self._items)

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def active_items(self) -> list[OrderItem]:
        return [i for i in self._items if i.status != OrderItemStatus.CANCELLED]

    # -- Factory ----------------------------------------------------------

    @staticmethod
    def place(
        order_id: OrderId,
        table: TableNumber,
        items: list[OrderItem],
    ) -> Order:
        """Factory: create a new order with initial items.

        Raises EmptyOrderError if items list is empty.
        """
        if not items:
            raise EmptyOrderError()

        order = Order(
            _id=order_id, _table=table, _items=list(items), _status=OrderStatus.OPEN
        )
        order._record_event(
            OrderPlaced(
                order_id=str(order_id),
                table_number=table.value,
                item_count=len(items),
            )
        )
        return order

    # -- Commands ---------------------------------------------------------

    def add_item(self, item: OrderItem) -> None:
        """Add an item to this open order."""
        self._assert_open()
        if not isinstance(item, OrderItem):
            raise InvalidFieldTypeError("Order.add_item", "item", "OrderItem")
        self._items.append(item)
        self._record_event(
            OrderItemAdded(
                order_id=str(self.id),
                order_item_id=str(item.id),
                menu_item_id=item.menu_item_id,
                quantity=item.quantity.value,
            )
        )

    def cancel_item(self, item_id: OrderItemId) -> None:
        """Cancel a specific item. If all active items become cancelled, auto-cancel the order."""
        self._assert_open()
        item = self._find_item(item_id)
        item.cancel()
        self._record_event(
            OrderItemCancelled(order_id=str(self.id), order_item_id=str(item_id))
        )
        if self._all_items_cancelled():
            self._status = OrderStatus.CANCELLED
            self._record_event(OrderCancelled(order_id=str(self.id)))

    def mark_item_ready(self, item_id: OrderItemId) -> None:
        """Mark an item as ready to serve."""
        self._assert_open()
        item = self._find_item(item_id)
        item.mark_ready()
        self._record_event(
            DishMarkedReady(order_id=str(self.id), order_item_id=str(item_id))
        )

    def complete(self) -> None:
        """Complete this order. All active items must be READY."""
        self._assert_open()
        active = [i for i in self._items if i.status != OrderItemStatus.CANCELLED]
        if not active or not all(i.status == OrderItemStatus.READY for i in active):
            raise OrderNotFullyReadyError(str(self.id))
        self._status = OrderStatus.COMPLETED
        self._record_event(OrderCompleted(order_id=str(self.id)))

    def cancel(self) -> None:
        """Cancel the entire order."""
        self._assert_open()
        for item in self._items:
            if item.status not in (OrderItemStatus.CANCELLED, OrderItemStatus.READY):
                item._status = OrderItemStatus.CANCELLED
        self._status = OrderStatus.CANCELLED
        self._record_event(OrderCancelled(order_id=str(self.id)))

    # -- Invariant guards -------------------------------------------------

    def _assert_open(self) -> None:
        if self._status != OrderStatus.OPEN:
            raise OrderNotOpenError(str(self.id), self._status.value)

    def _find_item(self, item_id: OrderItemId) -> OrderItem:
        for item in self._items:
            if item.id == item_id:
                return item
        raise OrderItemNotFoundError(str(self.id), str(item_id))

    def _all_items_cancelled(self) -> bool:
        return all(i.status == OrderItemStatus.CANCELLED for i in self._items)
