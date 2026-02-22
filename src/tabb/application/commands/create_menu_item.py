"""Create a menu item — command and handler."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from tabb.application.outbox import OutboxEntry
from tabb.application.ports.inbound.commands import Command, CommandHandler
from tabb.application.ports.outbound.unit_of_work import UnitOfWork
from tabb.domain.models.menu_item import MenuItem, MenuItemId
from tabb.domain.models.value_objects import Money
from tabb.domain.ports.id_generator import IdGenerator


@dataclass(frozen=True, kw_only=True)
class CreateMenuItemCommand(Command):
    """Command to create a new menu item."""

    menu_item_id: str
    name: str
    price: Decimal


class CreateMenuItemHandler(CommandHandler):
    """Creates a new menu item via the domain factory."""

    def __init__(self, uow: UnitOfWork, id_generator: IdGenerator) -> None:
        self._uow = uow
        self._id_generator = id_generator

    async def handle(self, command: Any) -> None:
        cmd: CreateMenuItemCommand = command

        async with self._uow:
            menu_item = MenuItem.create(
                item_id=MenuItemId(cmd.menu_item_id),
                name=cmd.name,
                price=Money(cmd.price),
            )

            await self._uow.menu_item_repository.save(menu_item)

            for event in menu_item.collect_events():
                entry = OutboxEntry.create(
                    entry_id=self._id_generator.generate(),
                    event=event,
                    aggregate_id=str(menu_item.id),
                    aggregate_type="MenuItem",
                )
                await self._uow.outbox_repository.save(entry)

            await self._uow.commit()
