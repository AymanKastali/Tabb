"""Get an order — query and handler."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from tabb.application.dto.order_dtos import OrderItemResult, OrderResult
from tabb.application.exceptions import OrderNotFoundError
from tabb.application.ports.inbound.queries import Query, QueryHandler
from tabb.application.ports.outbound.order_read_model_repository import (
    OrderReadModelRepository,
)


@dataclass(frozen=True, kw_only=True)
class GetOrderQuery(Query):
    """Query to retrieve an order by its ID."""

    order_id: str


class GetOrderHandler(QueryHandler):
    """Retrieves an order from the read model and maps it to a result DTO."""

    def __init__(self, order_read_model_repository: OrderReadModelRepository) -> None:
        self._read_repo = order_read_model_repository

    async def handle(self, query: Any) -> OrderResult:
        q: GetOrderQuery = query

        read_model = await self._read_repo.find_by_id(q.order_id)
        if read_model is None:
            raise OrderNotFoundError(q.order_id)

        return OrderResult(
            order_id=read_model.order_id,
            table_number=read_model.table_number,
            status=read_model.status,
            items=[
                OrderItemResult(
                    order_item_id=item.order_item_id,
                    menu_item_id=item.menu_item_id,
                    name=item.name,
                    unit_price=Decimal(item.unit_price),
                    quantity=item.quantity,
                    status=item.status,
                    total_price=Decimal(item.total_price),
                )
                for item in read_model.items
            ],
        )
