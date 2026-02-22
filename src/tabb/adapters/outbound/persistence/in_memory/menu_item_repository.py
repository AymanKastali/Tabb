"""In-memory MenuItem repository adapter with staged writes for UoW."""

from __future__ import annotations

import copy

from tabb.domain.models.menu_item import MenuItem, MenuItemId
from tabb.domain.ports.menu_item_repository import MenuItemRepository


class InMemoryMenuItemRepository(MenuItemRepository):
    """In-memory write-side repository for MenuItem aggregates.

    Supports staged writes for UoW integration.
    """

    def __init__(self, store: dict[str, MenuItem]) -> None:
        self._store = store
        self._staging: dict[str, MenuItem] = {}

    async def find_by_id(self, item_id: MenuItemId) -> MenuItem | None:
        key = str(item_id)
        if key in self._staging:
            return copy.deepcopy(self._staging[key])
        if key in self._store:
            return copy.deepcopy(self._store[key])
        return None

    async def save(self, item: MenuItem) -> None:
        self._staging[str(item.id)] = copy.deepcopy(item)

    def flush(self) -> None:
        """Apply staged writes to the committed store."""
        self._store.update(self._staging)
        self._staging.clear()

    def discard(self) -> None:
        """Discard staged writes."""
        self._staging.clear()
