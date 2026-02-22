"""Data transfer objects for menu item operations."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, kw_only=True)
class MenuItemResult:
    """Output DTO for a menu item."""

    menu_item_id: str
    name: str
    price: Decimal
    available: bool
