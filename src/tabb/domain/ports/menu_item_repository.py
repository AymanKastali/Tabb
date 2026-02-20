"""Repository port for the MenuItem aggregate."""

from abc import ABC, abstractmethod

from tabb.domain.models.menu_item import MenuItem, MenuItemId


class MenuItemRepository(ABC):
    """Abstract repository for MenuItem persistence."""

    @abstractmethod
    async def find_by_id(self, item_id: MenuItemId) -> MenuItem | None:
        """Find a menu item by its identity. Returns None if not found."""

    @abstractmethod
    async def save(self, item: MenuItem) -> None:
        """Persist a menu item (insert or update)."""

    @abstractmethod
    async def find_all_available(self) -> list[MenuItem]:
        """Return all currently available menu items."""
