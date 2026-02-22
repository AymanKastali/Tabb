"""In-memory read model repository for menu items."""

from __future__ import annotations

import copy

from tabb.application.ports.outbound.menu_item_read_model_repository import (
    MenuItemReadModelRepository,
)
from tabb.application.read_models.menu_item_read_model import MenuItemReadModel


class InMemoryMenuItemReadModelRepository(MenuItemReadModelRepository):
    """In-memory repository for menu item read models."""

    def __init__(self) -> None:
        self._store: dict[str, MenuItemReadModel] = {}

    async def find_by_id(self, menu_item_id: str) -> MenuItemReadModel | None:
        rm = self._store.get(menu_item_id)
        return copy.deepcopy(rm) if rm is not None else None

    async def find_all_available(self) -> list[MenuItemReadModel]:
        return [copy.deepcopy(rm) for rm in self._store.values() if rm.available]

    async def save(self, read_model: MenuItemReadModel) -> None:
        self._store[read_model.menu_item_id] = copy.deepcopy(read_model)
