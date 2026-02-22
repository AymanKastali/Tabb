"""Menu item projector — builds menu item read models from domain events."""

from __future__ import annotations

from tabb.application.ports.inbound.projector import Projector
from tabb.application.ports.outbound.menu_item_read_model_repository import (
    MenuItemReadModelRepository,
)
from tabb.application.read_models.menu_item_read_model import MenuItemReadModel


class MenuItemProjector(Projector):
    """Projects menu-item-related events into MenuItemReadModel."""

    def __init__(self, repository: MenuItemReadModelRepository) -> None:
        self._repo = repository

    def handles(self) -> list[str]:
        return [
            "MenuItemCreated",
            "MenuItemSoldOut",
            "MenuItemAvailable",
        ]

    async def project(self, event_type: str, event_data: dict[str, object]) -> None:
        handler = getattr(self, f"_handle_{event_type}", None)
        if handler is None:
            return
        await handler(event_data)

    async def _handle_MenuItemCreated(self, data: dict[str, object]) -> None:
        menu_item_id = str(data["menu_item_id"])
        existing = await self._repo.find_by_id(menu_item_id)
        if existing is not None:
            return  # idempotent

        read_model = MenuItemReadModel(
            menu_item_id=menu_item_id,
            name=str(data["name"]),
            price=str(data["price"]),
            available=True,
        )
        await self._repo.save(read_model)

    async def _handle_MenuItemSoldOut(self, data: dict[str, object]) -> None:
        menu_item_id = str(data["menu_item_id"])
        read_model = await self._repo.find_by_id(menu_item_id)
        if read_model is None:
            return

        read_model.available = False
        await self._repo.save(read_model)

    async def _handle_MenuItemAvailable(self, data: dict[str, object]) -> None:
        menu_item_id = str(data["menu_item_id"])
        read_model = await self._repo.find_by_id(menu_item_id)
        if read_model is None:
            return

        read_model.available = True
        await self._repo.save(read_model)
