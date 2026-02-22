"""Read model for menu items (CQRS query side)."""

from dataclasses import dataclass


@dataclass
class MenuItemReadModel:
    """Flat read model for a menu item."""

    menu_item_id: str
    name: str
    price: str
    available: bool
