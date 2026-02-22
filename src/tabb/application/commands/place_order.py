"""Place a new order — command and handler."""

from dataclasses import dataclass
from typing import Any

from tabb.application.dto.order_dtos import OrderItemRequest
from tabb.application.outbox import OutboxEntry
from tabb.application.ports.inbound.commands import Command, CommandHandler
from tabb.application.ports.outbound.unit_of_work import UnitOfWork
from tabb.domain.exceptions.business import EmptyOrderError
from tabb.domain.models.menu_item import MenuItemId
from tabb.domain.models.order import Order, OrderId, OrderItemId
from tabb.domain.models.value_objects import Money, Quantity, TableNumber
from tabb.domain.ports.id_generator import IdGenerator
from tabb.domain.services.order_service import OrderDomainService


@dataclass(frozen=True, kw_only=True)
class PlaceOrderCommand(Command):
    """Command to place a new order."""

    order_id: str
    table_number: int
    items: list[OrderItemRequest]


class PlaceOrderHandler(CommandHandler):
    """Creates a new order after verifying menu item availability."""

    def __init__(
        self,
        uow: UnitOfWork,
        id_generator: IdGenerator,
    ) -> None:
        self._uow = uow
        self._id_generator = id_generator

    async def handle(self, command: Any) -> None:
        cmd: PlaceOrderCommand = command

        if not cmd.items:
            raise EmptyOrderError()

        async with self._uow:
            requested_menu_ids = [MenuItemId(item.menu_item_id) for item in cmd.items]

            menu_items = [
                mi
                for mid in requested_menu_ids
                if (mi := await self._uow.menu_item_repository.find_by_id(mid))
                is not None
            ]

            OrderDomainService.verify_items_available(requested_menu_ids, menu_items)

            order = Order.place(
                order_id=OrderId(cmd.order_id),
                table=TableNumber(cmd.table_number),
            )

            for item in cmd.items:
                order.add_item(
                    OrderItemId(self._id_generator.generate()),
                    MenuItemId(item.menu_item_id),
                    item.name,
                    Money(item.unit_price),
                    Quantity(item.quantity),
                )

            await self._uow.order_repository.save(order)

            for event in order.collect_events():
                entry = OutboxEntry.create(
                    entry_id=self._id_generator.generate(),
                    event=event,
                    aggregate_id=str(order.id),
                    aggregate_type="Order",
                )
                await self._uow.outbox_repository.save(entry)

            await self._uow.commit()
