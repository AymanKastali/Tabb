"""Read model for orders (CQRS query side)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OrderItemReadModel:
    """Flat read model for an order item."""

    order_item_id: str
    menu_item_id: str
    name: str
    unit_price: str
    quantity: int
    status: str
    total_price: str


@dataclass
class OrderReadModel:
    """Flat read model for an order."""

    order_id: str
    table_number: int
    status: str
    items: list[OrderItemReadModel] = field(default_factory=list)
