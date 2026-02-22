"""Cancel an order — command and handler."""

from dataclasses import dataclass
from typing import Any

from tabb.application.exceptions import OrderNotFoundError
from tabb.application.outbox import OutboxEntry
from tabb.application.ports.inbound.commands import Command, CommandHandler
from tabb.application.ports.outbound.unit_of_work import UnitOfWork
from tabb.domain.models.order import OrderId
from tabb.domain.ports.id_generator import IdGenerator


@dataclass(frozen=True, kw_only=True)
class CancelOrderCommand(Command):
    """Command to cancel an entire order."""

    order_id: str


class CancelOrderHandler(CommandHandler):
    """Cancels an entire order."""

    def __init__(self, uow: UnitOfWork, id_generator: IdGenerator) -> None:
        self._uow = uow
        self._id_generator = id_generator

    async def handle(self, command: Any) -> None:
        cmd: CancelOrderCommand = command

        async with self._uow:
            order = await self._uow.order_repository.find_by_id(OrderId(cmd.order_id))
            if order is None:
                raise OrderNotFoundError(cmd.order_id)

            order.cancel()
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
