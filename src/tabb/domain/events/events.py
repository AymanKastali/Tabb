"""Domain events for tabb."""

from dataclasses import dataclass

from tabb.domain.events.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class OrderPlaced(DomainEvent):
    """Raised when a new order is placed."""

    order_id: str
    table_number: int
    item_count: int


@dataclass(frozen=True, kw_only=True)
class OrderItemAdded(DomainEvent):
    """Raised when an item is added to an existing open order."""

    order_id: str
    order_item_id: str
    menu_item_id: str
    quantity: int


@dataclass(frozen=True, kw_only=True)
class OrderItemCancelled(DomainEvent):
    """Raised when an item is cancelled from an order."""

    order_id: str
    order_item_id: str


@dataclass(frozen=True, kw_only=True)
class DishMarkedReady(DomainEvent):
    """Raised when a dish (order item) is marked as ready to serve."""

    order_id: str
    order_item_id: str


@dataclass(frozen=True, kw_only=True)
class OrderCompleted(DomainEvent):
    """Raised when all items in an order are served and the order is completed."""

    order_id: str


@dataclass(frozen=True, kw_only=True)
class OrderCancelled(DomainEvent):
    """Raised when an order is cancelled."""

    order_id: str


@dataclass(frozen=True, kw_only=True)
class MenuItemSoldOut(DomainEvent):
    """Raised when a menu item is marked as sold out."""

    menu_item_id: str


@dataclass(frozen=True, kw_only=True)
class MenuItemAvailable(DomainEvent):
    """Raised when a menu item becomes available again."""

    menu_item_id: str
