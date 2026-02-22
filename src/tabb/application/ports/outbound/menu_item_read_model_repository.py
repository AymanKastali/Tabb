"""Outbound port — read model repository for menu items."""

from __future__ import annotations

from abc import ABC, abstractmethod

from tabb.application.read_models.menu_item_read_model import MenuItemReadModel


class MenuItemReadModelRepository(ABC):
    """Abstract repository for the menu item read model."""

    @abstractmethod
    async def find_by_id(self, menu_item_id: str) -> MenuItemReadModel | None:
        """Find a menu item read model by its ID."""

    @abstractmethod
    async def find_all_available(self) -> list[MenuItemReadModel]:
        """Return all currently available menu item read models."""

    @abstractmethod
    async def save(self, read_model: MenuItemReadModel) -> None:
        """Persist a menu item read model (insert or update)."""
