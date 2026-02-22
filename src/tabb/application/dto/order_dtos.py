"""Data transfer objects for order operations."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, kw_only=True)
class OrderItemRequest:
    """Input DTO for an item within an order placement."""

    menu_item_id: str
    name: str
    unit_price: Decimal
    quantity: int


@dataclass(frozen=True, kw_only=True)
class OrderItemResult:
    """Output DTO for an order item."""

    order_item_id: str
    menu_item_id: str
    name: str
    unit_price: Decimal
    quantity: int
    status: str
    total_price: Decimal


@dataclass(frozen=True, kw_only=True)
class OrderResult:
    """Output DTO for an order."""

    order_id: str
    table_number: int
    status: str
    items: list[OrderItemResult]
