"""Mark a menu item as sold out — command and handler."""

from dataclasses import dataclass
from typing import Any

from tabb.application.exceptions import MenuItemNotFoundError
from tabb.application.outbox import OutboxEntry
from tabb.application.ports.inbound.commands import Command, CommandHandler
from tabb.application.ports.outbound.unit_of_work import UnitOfWork
from tabb.domain.models.menu_item import MenuItemId
from tabb.domain.ports.id_generator import IdGenerator


@dataclass(frozen=True, kw_only=True)
class MarkMenuItemSoldOutCommand(Command):
    """Command to mark a menu item as sold out."""

    menu_item_id: str


class MarkMenuItemSoldOutHandler(CommandHandler):
    """Marks a menu item as sold out."""

    def __init__(self, uow: UnitOfWork, id_generator: IdGenerator) -> None:
        self._uow = uow
        self._id_generator = id_generator

    async def handle(self, command: Any) -> None:
        cmd: MarkMenuItemSoldOutCommand = command

        async with self._uow:
            menu_item = await self._uow.menu_item_repository.find_by_id(
                MenuItemId(cmd.menu_item_id)
            )
            if menu_item is None:
                raise MenuItemNotFoundError(cmd.menu_item_id)

            menu_item.mark_sold_out()
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
