"""MenuItem aggregate — manages dish availability."""

from dataclasses import dataclass
from typing import Self

from tabb.domain.events.events import (
    MenuItemAvailable,
    MenuItemCreated,
    MenuItemSoldOut,
)
from tabb.domain.exceptions.validation import InvalidFieldTypeError, RequiredFieldError
from tabb.domain.models.value_objects import Money
from tabb.domain.shared.building_blocks import AggregateRoot, Id


class MenuItemId(Id[str]):
    """Identity for a menu item."""


@dataclass
class MenuItem(AggregateRoot[MenuItemId]):
    """Aggregate root for a dish on the restaurant menu.

    Controls availability independently of orders, allowing concurrent
    changes without contention on the Order aggregate.

    Must be created via the ``create`` factory method.
    """

    _name: str
    _price: Money
    _available: bool = True

    def __post_init__(self) -> None:
        cls_name = type(self).__name__

        if not isinstance(self._id, MenuItemId):
            raise InvalidFieldTypeError(cls_name, "id", "MenuItemId")
        if not isinstance(self._name, str) or not self._name.strip():
            raise RequiredFieldError(cls_name, "name")
        if not isinstance(self._price, Money):
            raise InvalidFieldTypeError(cls_name, "price", "Money")
        if not isinstance(self._available, bool):
            raise InvalidFieldTypeError(cls_name, "available", "bool")

    @property
    def name(self) -> str:
        return self._name

    @property
    def price(self) -> Money:
        return self._price

    @property
    def available(self) -> bool:
        return self._available

    @classmethod
    def create(cls, item_id: MenuItemId, name: str, price: Money) -> Self:
        """Factory: create a new available menu item."""
        item = cls(_id=item_id, _name=name, _price=price, _available=True)
        item._record_event(
            MenuItemCreated(
                menu_item_id=str(item_id),
                name=name,
                price=str(price.amount),
            )
        )
        return item

    def mark_sold_out(self) -> None:
        """Mark this menu item as sold out."""
        if not self._available:
            return
        self._available = False
        self._record_event(MenuItemSoldOut(menu_item_id=str(self.id)))

    def mark_available(self) -> None:
        """Mark this menu item as available again."""
        if self._available:
            return
        self._available = True
        self._record_event(MenuItemAvailable(menu_item_id=str(self.id)))
