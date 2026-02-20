"""Dependency injection wiring for tabb.

This module wires port interfaces (abstractions) to their concrete
adapter implementations using FastAPI's Depends() mechanism.
"""

from tabb.adapters.outbound.persistence.postgres.config import get_session

__all__ = ["get_session"]

# Example: wiring a repository for an Order aggregate
#
#   from fastapi import Depends
#   from sqlalchemy.ext.asyncio import AsyncSession
#   from tabb.adapters.outbound.persistence.postgres.repositories import (
#       SQLAlchemyOrderRepository,
#   )
#   from tabb.application.ports.outbound.order_repository import OrderRepository
#
#   async def get_order_repository(
#       session: AsyncSession = Depends(get_session),
#   ) -> OrderRepository:
#       return SQLAlchemyOrderRepository(session=session)

