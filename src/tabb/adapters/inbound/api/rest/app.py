"""FastAPI application factory for tabb."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from tabb.adapters.config.settings import settings
from tabb.adapters.outbound.logging.logger import setup_logging

from tabb.adapters.outbound.persistence.postgres.config import database


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""

    await database.connect()

    yield

    await database.disconnect()



def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    """Register API route handlers."""

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": settings.app_name}
