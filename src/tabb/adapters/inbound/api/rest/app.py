"""FastAPI application factory for tabb — composition root."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from tabb.adapters.config.settings import settings
from tabb.adapters.outbound.logging.logger import setup_logging
from tabb.adapters.outbound.persistence.in_memory.menu_item_read_model_repository import (
    InMemoryMenuItemReadModelRepository,
)
from tabb.adapters.outbound.persistence.in_memory.order_read_model_repository import (
    InMemoryOrderReadModelRepository,
)
from tabb.adapters.outbound.persistence.in_memory.outbox_repository import (
    InMemoryOutboxRepository,
)
from tabb.adapters.outbound.projectors.menu_item_projector import MenuItemProjector
from tabb.adapters.outbound.projectors.order_projector import OrderProjector
from tabb.adapters.outbound.workers.background_outbox_worker import AsyncOutboxWorker
from tabb.adapters.outbound.workers.outbox_processor import InMemoryOutboxProcessor
from tabb.application.outbox import OutboxEntry


setup_logging()

logger = logging.getLogger("tabb")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    worker: AsyncOutboxWorker = app.state.outbox_worker
    await worker.start()
    try:
        yield
    finally:
        await worker.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Shared in-memory stores (scoped to this app instance)
    outbox_store: list[OutboxEntry] = []

    # Read-model repositories
    order_read_repo = InMemoryOrderReadModelRepository()
    menu_item_read_repo = InMemoryMenuItemReadModelRepository()

    # Projectors
    projectors = [
        OrderProjector(order_read_repo),
        MenuItemProjector(menu_item_read_repo),
    ]

    # Outbox processor
    outbox_repo = InMemoryOutboxRepository(outbox_store)
    processor = InMemoryOutboxProcessor(
        outbox_repository=outbox_repo,
        projectors=projectors,
        logger=logger,
    )

    # Background worker
    worker = AsyncOutboxWorker(
        processor=processor,
        interval_seconds=settings.outbox_poll_interval_seconds,
        logger=logger,
    )

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.state.outbox_worker = worker

    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    """Register API route handlers."""

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": settings.app_name}
