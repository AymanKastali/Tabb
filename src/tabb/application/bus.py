"""In-process CQRS bus implementations (pure Python)."""

from collections.abc import Callable
from typing import Any

from tabb.application.ports.inbound.commands import Command, CommandBus, CommandHandler
from tabb.application.ports.inbound.queries import Query, QueryBus, QueryHandler


class InProcessCommandBus(CommandBus):
    """Routes commands to handler factories. Pure Python, no external deps.

    Handler factories (callables returning CommandHandler) are used because
    handlers hold per-request repository references injected at dispatch time.
    """

    def __init__(self) -> None:
        self._registry: dict[type[Command], Callable[[], CommandHandler]] = {}

    def register(
        self,
        command_type: type[Command],
        handler_factory: Callable[[], CommandHandler],
    ) -> None:
        """Register a handler factory for a command type.

        Raises ValueError if the command type is already registered.
        """
        if command_type in self._registry:
            raise ValueError(f"Handler already registered for {command_type.__name__}")
        self._registry[command_type] = handler_factory

    async def dispatch(self, command: Command) -> Any:
        """Create a handler via its factory and execute the command.

        Raises LookupError if no handler is registered for the command type.
        """
        command_type = type(command)
        factory = self._registry.get(command_type)
        if factory is None:
            raise LookupError(f"No handler registered for {command_type.__name__}")
        handler = factory()
        return await handler.handle(command)


class InProcessQueryBus(QueryBus):
    """Routes queries to handler factories. Pure Python, no external deps."""

    def __init__(self) -> None:
        self._registry: dict[type[Query], Callable[[], QueryHandler]] = {}

    def register(
        self,
        query_type: type[Query],
        handler_factory: Callable[[], QueryHandler],
    ) -> None:
        """Register a handler factory for a query type.

        Raises ValueError if the query type is already registered.
        """
        if query_type in self._registry:
            raise ValueError(f"Handler already registered for {query_type.__name__}")
        self._registry[query_type] = handler_factory

    async def dispatch(self, query: Query) -> Any:
        """Create a handler via its factory and execute the query.

        Raises LookupError if no handler is registered for the query type.
        """
        query_type = type(query)
        factory = self._registry.get(query_type)
        if factory is None:
            raise LookupError(f"No handler registered for {query_type.__name__}")
        handler = factory()
        return await handler.handle(query)
