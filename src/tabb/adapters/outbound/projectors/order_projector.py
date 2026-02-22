"""Order projector — builds order read models from domain events."""

from __future__ import annotations

from decimal import Decimal

from tabb.application.ports.inbound.projector import Projector
from tabb.application.ports.outbound.order_read_model_repository import (
    OrderReadModelRepository,
)
from tabb.application.read_models.order_read_model import (
    OrderItemReadModel,
    OrderReadModel,
)


class OrderProjector(Projector):
    """Projects order-related events into OrderReadModel."""

    def __init__(self, repository: OrderReadModelRepository) -> None:
        self._repo = repository

    def handles(self) -> list[str]:
        return [
            "OrderPlaced",
            "OrderItemAdded",
            "DishMarkedReady",
            "OrderItemCancelled",
            "OrderCompleted",
            "OrderCancelled",
        ]

    async def project(self, event_type: str, event_data: dict[str, object]) -> None:
        handler = getattr(self, f"_handle_{event_type}", None)
        if handler is None:
            return
        await handler(event_data)

    async def _handle_OrderPlaced(self, data: dict[str, object]) -> None:
        order_id = str(data["order_id"])
        existing = await self._repo.find_by_id(order_id)
        if existing is not None:
            return  # idempotent
        read_model = OrderReadModel(
            order_id=order_id,
            table_number=int(str(data["table_number"])),
            status="open",
            items=[],
        )
        await self._repo.save(read_model)

    async def _handle_OrderItemAdded(self, data: dict[str, object]) -> None:
        order_id = str(data["order_id"])
        read_model = await self._repo.find_by_id(order_id)
        if read_model is None:
            return

        order_item_id = str(data["order_item_id"])
        # idempotent: skip if item already exists
        if any(i.order_item_id == order_item_id for i in read_model.items):
            return

        quantity = int(str(data["quantity"]))
        unit_price = str(data["unit_price"])
        total_price = str(Decimal(unit_price) * quantity)

        read_model.items.append(
            OrderItemReadModel(
                order_item_id=order_item_id,
                menu_item_id=str(data["menu_item_id"]),
                name=str(data["name"]),
                unit_price=unit_price,
                quantity=quantity,
                status="pending",
                total_price=total_price,
            )
        )
        await self._repo.save(read_model)

    async def _handle_DishMarkedReady(self, data: dict[str, object]) -> None:
        order_id = str(data["order_id"])
        read_model = await self._repo.find_by_id(order_id)
        if read_model is None:
            return

        order_item_id = str(data["order_item_id"])
        for item in read_model.items:
            if item.order_item_id == order_item_id:
                item.status = "ready"
                break
        await self._repo.save(read_model)

    async def _handle_OrderItemCancelled(self, data: dict[str, object]) -> None:
        order_id = str(data["order_id"])
        read_model = await self._repo.find_by_id(order_id)
        if read_model is None:
            return

        order_item_id = str(data["order_item_id"])
        for item in read_model.items:
            if item.order_item_id == order_item_id:
                item.status = "cancelled"
                break
        await self._repo.save(read_model)

    async def _handle_OrderCompleted(self, data: dict[str, object]) -> None:
        order_id = str(data["order_id"])
        read_model = await self._repo.find_by_id(order_id)
        if read_model is None:
            return

        read_model.status = "completed"
        await self._repo.save(read_model)

    async def _handle_OrderCancelled(self, data: dict[str, object]) -> None:
        order_id = str(data["order_id"])
        read_model = await self._repo.find_by_id(order_id)
        if read_model is None:
            return

        read_model.status = "cancelled"
        await self._repo.save(read_model)
