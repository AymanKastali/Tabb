"""Tests for in-process CQRS bus implementations."""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest

from tabb.application.bus import InProcessCommandBus, InProcessQueryBus
from tabb.application.ports.inbound.commands import Command, CommandHandler
from tabb.application.ports.inbound.queries import Query, QueryHandler

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class _StubCommand(Command):
    value: str


@dataclass(frozen=True, kw_only=True)
class _UnregisteredCommand(Command):
    pass


class _StubCommandHandler(CommandHandler):
    def __init__(self) -> None:
        self.handle_mock = AsyncMock(return_value="handled")

    async def handle(self, command: Any) -> Any:
        return await self.handle_mock(command)


@dataclass(frozen=True, kw_only=True)
class _StubQuery(Query):
    value: str


@dataclass(frozen=True, kw_only=True)
class _UnregisteredQuery(Query):
    pass


class _StubQueryHandler(QueryHandler):
    def __init__(self) -> None:
        self.handle_mock = AsyncMock(return_value="result")

    async def handle(self, query: Any) -> Any:
        return await self.handle_mock(query)


# ---------------------------------------------------------------------------
# CommandBus Tests
# ---------------------------------------------------------------------------


class TestInProcessCommandBus:
    @pytest.fixture()
    def bus(self) -> InProcessCommandBus:
        return InProcessCommandBus()

    async def test_dispatch_routes_to_handler(self, bus: InProcessCommandBus) -> None:
        handler = _StubCommandHandler()
        bus.register(_StubCommand, lambda: handler)

        cmd = _StubCommand(value="test")
        result = await bus.dispatch(cmd)

        assert result == "handled"
        handler.handle_mock.assert_awaited_once_with(cmd)

    async def test_dispatch_unregistered_command_raises(
        self, bus: InProcessCommandBus
    ) -> None:
        with pytest.raises(LookupError, match="No handler registered"):
            await bus.dispatch(_UnregisteredCommand())

    async def test_duplicate_registration_raises(
        self, bus: InProcessCommandBus
    ) -> None:
        bus.register(_StubCommand, _StubCommandHandler)
        with pytest.raises(ValueError, match="already registered"):
            bus.register(_StubCommand, _StubCommandHandler)

    async def test_factory_called_per_dispatch(self, bus: InProcessCommandBus) -> None:
        call_count = 0
        handlers: list[_StubCommandHandler] = []

        def counting_factory() -> _StubCommandHandler:
            nonlocal call_count
            call_count += 1
            h = _StubCommandHandler()
            handlers.append(h)
            return h

        bus.register(_StubCommand, counting_factory)

        await bus.dispatch(_StubCommand(value="a"))
        await bus.dispatch(_StubCommand(value="b"))

        assert call_count == 2
        assert len(handlers) == 2
        assert handlers[0] is not handlers[1]


# ---------------------------------------------------------------------------
# QueryBus Tests
# ---------------------------------------------------------------------------


class TestInProcessQueryBus:
    @pytest.fixture()
    def bus(self) -> InProcessQueryBus:
        return InProcessQueryBus()

    async def test_dispatch_routes_to_handler(self, bus: InProcessQueryBus) -> None:
        handler = _StubQueryHandler()
        bus.register(_StubQuery, lambda: handler)

        query = _StubQuery(value="test")
        result = await bus.dispatch(query)

        assert result == "result"
        handler.handle_mock.assert_awaited_once_with(query)

    async def test_dispatch_unregistered_query_raises(
        self, bus: InProcessQueryBus
    ) -> None:
        with pytest.raises(LookupError, match="No handler registered"):
            await bus.dispatch(_UnregisteredQuery())

    async def test_duplicate_registration_raises(self, bus: InProcessQueryBus) -> None:
        bus.register(_StubQuery, _StubQueryHandler)
        with pytest.raises(ValueError, match="already registered"):
            bus.register(_StubQuery, _StubQueryHandler)
