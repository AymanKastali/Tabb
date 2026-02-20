"""SQLAlchemy repository adapters for tabb.

This module is where you define your concrete repository implementations.
Each Aggregate Root in your domain should have its own repository class.

Example
-------
Suppose you have an ``Order`` aggregate and an outbound port::

    # application/ports/outbound/order_repository.py
    class OrderRepository(ABC):
        @abstractmethod
        async def find_by_id(self, order_id: UUID) -> Order | None: ...
        @abstractmethod
        async def save(self, order: Order) -> None: ...

Then implement it here::

    class SQLAlchemyOrderRepository(OrderRepository):
        def __init__(self, session: AsyncSession) -> None:
            self._session = session

        async def find_by_id(self, order_id: UUID) -> Order | None:
            ...

        async def save(self, order: Order) -> None:
            ...

Wire it up in ``dependencies.py`` via FastAPI's ``Depends()``.
"""

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401
