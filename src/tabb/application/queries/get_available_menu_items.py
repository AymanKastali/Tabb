"""Get available menu items — query and handler."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from tabb.application.dto.menu_item_dtos import MenuItemResult
from tabb.application.ports.inbound.queries import Query, QueryHandler
from tabb.application.ports.outbound.menu_item_read_model_repository import (
    MenuItemReadModelRepository,
)


@dataclass(frozen=True, kw_only=True)
class GetAvailableMenuItemsQuery(Query):
    """Query to retrieve all available menu items."""


class GetAvailableMenuItemsHandler(QueryHandler):
    """Retrieves all available menu items from the read model."""

    def __init__(
        self, menu_item_read_model_repository: MenuItemReadModelRepository
    ) -> None:
        self._read_repo = menu_item_read_model_repository

    async def handle(self, query: Any) -> list[MenuItemResult]:
        read_models = await self._read_repo.find_all_available()

        return [
            MenuItemResult(
                menu_item_id=rm.menu_item_id,
                name=rm.name,
                price=Decimal(rm.price),
                available=rm.available,
            )
            for rm in read_models
        ]
