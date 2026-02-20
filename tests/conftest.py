"""Shared test fixtures for tabb."""

import pytest
from httpx import ASGITransport, AsyncClient

from tabb.adapters.inbound.api.rest.app import create_app


@pytest.fixture
def app():
    """Create a test FastAPI application instance."""
    return create_app()


@pytest.fixture
async def client(app):
    """Create an async test client for the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
