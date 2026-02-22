"""Integration test: end-to-end CQRS flow with eventual consistency.

Demonstrates:
1. Commands write to the write DB + outbox
2. Queries return nothing before outbox processes (eventual consistency)
3. Outbox processor runs, projects events to read DB
4. Queries now return projected data
5. Failed projections retry and eventually succeed or dead-letter
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from tabb.adapters.outbound.id_generator.uuid_generator import UuidIdGenerator
from tabb.adapters.outbound.persistence.in_memory.menu_item_read_model_repository import (
    InMemoryMenuItemReadModelRepository,
)
from tabb.adapters.outbound.persistence.in_memory.order_read_model_repository import (
    InMemoryOrderReadModelRepository,
)
from tabb.adapters.outbound.persistence.in_memory.outbox_repository import (
    InMemoryOutboxRepository,
)
from tabb.adapters.outbound.persistence.in_memory.unit_of_work import (
    InMemoryUnitOfWork,
)
from tabb.adapters.outbound.projectors.menu_item_projector import MenuItemProjector
from tabb.adapters.outbound.projectors.order_projector import OrderProjector
from tabb.adapters.outbound.workers.outbox_processor import InMemoryOutboxProcessor
from tabb.application.commands.cancel_order import (
    CancelOrderCommand,
    CancelOrderHandler,
)
from tabb.application.commands.complete_order import (
    CompleteOrderCommand,
    CompleteOrderHandler,
)
from tabb.application.commands.create_menu_item import (
    CreateMenuItemCommand,
    CreateMenuItemHandler,
)
from tabb.application.commands.mark_item_ready import (
    MarkItemReadyCommand,
    MarkItemReadyHandler,
)
from tabb.application.commands.mark_menu_item_sold_out import (
    MarkMenuItemSoldOutCommand,
    MarkMenuItemSoldOutHandler,
)
from tabb.application.commands.place_order import PlaceOrderCommand, PlaceOrderHandler
from tabb.application.dto.order_dtos import OrderItemRequest
from tabb.application.exceptions import OrderNotFoundError
from tabb.application.outbox import OutboxEntryStatus
from tabb.application.queries.get_available_menu_items import (
    GetAvailableMenuItemsHandler,
    GetAvailableMenuItemsQuery,
)
from tabb.application.queries.get_order import GetOrderHandler, GetOrderQuery

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Shared in-memory stores (simulate databases)
# ---------------------------------------------------------------------------


@pytest.fixture()
def stores():
    """Create fresh shared stores for each test."""
    return {
        "orders": {},
        "menu_items": {},
        "outbox": [],
    }


@pytest.fixture()
def order_read_repo():
    return InMemoryOrderReadModelRepository()


@pytest.fixture()
def menu_item_read_repo():
    return InMemoryMenuItemReadModelRepository()


@pytest.fixture()
def id_generator():
    return UuidIdGenerator()


@pytest.fixture()
def outbox_processor(stores, order_read_repo, menu_item_read_repo):
    outbox_repo = InMemoryOutboxRepository(stores["outbox"])
    return InMemoryOutboxProcessor(
        outbox_repository=outbox_repo,
        projectors=[
            OrderProjector(order_read_repo),
            MenuItemProjector(menu_item_read_repo),
        ],
    )


def _uow(stores):
    return InMemoryUnitOfWork(
        order_store=stores["orders"],
        menu_item_store=stores["menu_items"],
        outbox_store=stores["outbox"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCqrsFlow:
    """End-to-end: CreateMenuItem -> PlaceOrder -> MarkReady -> Complete."""

    async def test_full_order_lifecycle(
        self,
        stores,
        order_read_repo,
        menu_item_read_repo,
        id_generator,
        outbox_processor,
    ):
        # Step 1: Create a menu item
        handler = CreateMenuItemHandler(_uow(stores), id_generator)
        await handler.handle(
            CreateMenuItemCommand(
                menu_item_id="m-1", name="Burger", price=Decimal("9.99")
            )
        )

        # Query side: nothing yet (eventual consistency)
        query_handler = GetAvailableMenuItemsHandler(menu_item_read_repo)
        result = await query_handler.handle(GetAvailableMenuItemsQuery())
        assert result == []

        # Step 2: Process outbox -> projects MenuItemCreated to read model
        processed = await outbox_processor.process_pending()
        assert processed == 1

        # Now query side sees the menu item
        result = await query_handler.handle(GetAvailableMenuItemsQuery())
        assert len(result) == 1
        assert result[0].menu_item_id == "m-1"
        assert result[0].name == "Burger"
        assert result[0].price == Decimal("9.99")

        # Step 3: Place an order
        handler = PlaceOrderHandler(_uow(stores), id_generator)
        await handler.handle(
            PlaceOrderCommand(
                order_id="o-1",
                table_number=5,
                items=[
                    OrderItemRequest(
                        menu_item_id="m-1",
                        name="Burger",
                        unit_price=Decimal("9.99"),
                        quantity=2,
                    )
                ],
            )
        )

        # Query side: order not visible yet
        order_query_handler = GetOrderHandler(order_read_repo)
        with pytest.raises(OrderNotFoundError):
            await order_query_handler.handle(GetOrderQuery(order_id="o-1"))

        # Step 4: Process outbox -> projects OrderPlaced + OrderItemAdded
        processed = await outbox_processor.process_pending()
        assert processed >= 2

        # Now query side sees the order
        order_result = await order_query_handler.handle(GetOrderQuery(order_id="o-1"))
        assert order_result.order_id == "o-1"
        assert order_result.table_number == 5
        assert order_result.status == "open"
        assert len(order_result.items) == 1
        assert order_result.items[0].name == "Burger"
        assert order_result.items[0].unit_price == Decimal("9.99")
        assert order_result.items[0].quantity == 2
        assert order_result.items[0].status == "pending"

        # Step 5: Mark item ready
        item_id = order_result.items[0].order_item_id
        handler = MarkItemReadyHandler(_uow(stores), id_generator)
        await handler.handle(
            MarkItemReadyCommand(order_id="o-1", order_item_id=item_id)
        )
        await outbox_processor.process_pending()

        order_result = await order_query_handler.handle(GetOrderQuery(order_id="o-1"))
        assert order_result.items[0].status == "ready"

        # Step 6: Complete the order
        handler = CompleteOrderHandler(_uow(stores), id_generator)
        await handler.handle(CompleteOrderCommand(order_id="o-1"))
        await outbox_processor.process_pending()

        order_result = await order_query_handler.handle(GetOrderQuery(order_id="o-1"))
        assert order_result.status == "completed"

    async def test_cancel_order_flow(
        self,
        stores,
        order_read_repo,
        menu_item_read_repo,
        id_generator,
        outbox_processor,
    ):
        # Create menu item and process
        handler = CreateMenuItemHandler(_uow(stores), id_generator)
        await handler.handle(
            CreateMenuItemCommand(
                menu_item_id="m-1", name="Fries", price=Decimal("4.99")
            )
        )
        await outbox_processor.process_pending()

        # Place order and process
        handler = PlaceOrderHandler(_uow(stores), id_generator)
        await handler.handle(
            PlaceOrderCommand(
                order_id="o-2",
                table_number=3,
                items=[
                    OrderItemRequest(
                        menu_item_id="m-1",
                        name="Fries",
                        unit_price=Decimal("4.99"),
                        quantity=1,
                    )
                ],
            )
        )
        await outbox_processor.process_pending()

        # Cancel order and process
        handler = CancelOrderHandler(_uow(stores), id_generator)
        await handler.handle(CancelOrderCommand(order_id="o-2"))
        await outbox_processor.process_pending()

        order_query_handler = GetOrderHandler(order_read_repo)
        order_result = await order_query_handler.handle(GetOrderQuery(order_id="o-2"))
        assert order_result.status == "cancelled"

    async def test_mark_menu_item_sold_out(
        self, stores, menu_item_read_repo, id_generator, outbox_processor
    ):
        # Create menu item and process
        handler = CreateMenuItemHandler(_uow(stores), id_generator)
        await handler.handle(
            CreateMenuItemCommand(
                menu_item_id="m-2", name="Salad", price=Decimal("7.50")
            )
        )
        await outbox_processor.process_pending()

        query_handler = GetAvailableMenuItemsHandler(menu_item_read_repo)
        result = await query_handler.handle(GetAvailableMenuItemsQuery())
        assert len(result) == 1

        # Mark sold out and process
        handler = MarkMenuItemSoldOutHandler(_uow(stores), id_generator)
        await handler.handle(MarkMenuItemSoldOutCommand(menu_item_id="m-2"))
        await outbox_processor.process_pending()

        result = await query_handler.handle(GetAvailableMenuItemsQuery())
        assert len(result) == 0


class TestOutboxRetry:
    """Tests retry and dead-lettering behavior."""

    async def test_failed_projection_retries(
        self, stores, order_read_repo, menu_item_read_repo, id_generator
    ):
        # Create menu item to generate an outbox entry
        handler = CreateMenuItemHandler(_uow(stores), id_generator)
        await handler.handle(
            CreateMenuItemCommand(
                menu_item_id="m-1", name="Burger", price=Decimal("9.99")
            )
        )

        # Verify outbox has a pending entry
        assert len(stores["outbox"]) == 1
        entry = stores["outbox"][0]
        assert entry.status == OutboxEntryStatus.PENDING

        # Create a projector that fails
        class FailingProjector:
            def handles(self):
                return ["MenuItemCreated"]

            async def project(self, event_type, event_data):
                raise RuntimeError("Simulated failure")

        outbox_repo = InMemoryOutboxRepository(stores["outbox"])
        processor = InMemoryOutboxProcessor(
            outbox_repository=outbox_repo,
            projectors=[FailingProjector()],
        )

        # First failure
        processed = await processor.process_pending()
        assert processed == 0
        assert entry.status == OutboxEntryStatus.FAILED
        assert entry.retry_count == 1

        # Simulate backoff elapsed so entry is re-fetched
        entry._next_retry_at = datetime.now(UTC) - timedelta(seconds=1)

        # Second failure
        await processor.process_pending()
        assert entry.retry_count == 2

        # Simulate backoff elapsed again
        entry._next_retry_at = datetime.now(UTC) - timedelta(seconds=1)

        # Third failure -> dead-lettered
        await processor.process_pending()
        assert entry.status == OutboxEntryStatus.DEAD_LETTERED
        assert entry.retry_count == 3

        # No longer picked up for processing
        entries = await outbox_repo.find_pending()
        assert len(entries) == 0

    async def test_failed_entry_recovers_on_retry(
        self, stores, order_read_repo, menu_item_read_repo, id_generator
    ):
        """Fail → backoff blocks immediate retry → simulate time → succeed."""
        # Create menu item to generate an outbox entry
        handler = CreateMenuItemHandler(_uow(stores), id_generator)
        await handler.handle(
            CreateMenuItemCommand(
                menu_item_id="m-1", name="Burger", price=Decimal("9.99")
            )
        )

        entry = stores["outbox"][0]
        assert entry.status == OutboxEntryStatus.PENDING

        # Create a projector that fails on first call, succeeds after
        call_count = 0

        class RecoveringProjector:
            def handles(self):
                return ["MenuItemCreated"]

            async def project(self, event_type, event_data):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("Temporary failure")
                # Delegate to real projector on recovery
                real = MenuItemProjector(menu_item_read_repo)
                await real.project(event_type, event_data)

        outbox_repo = InMemoryOutboxRepository(stores["outbox"])
        processor = InMemoryOutboxProcessor(
            outbox_repository=outbox_repo,
            projectors=[RecoveringProjector()],
        )

        # First attempt: fails
        processed = await processor.process_pending()
        assert processed == 0
        assert entry.status == OutboxEntryStatus.FAILED
        assert entry.retry_count == 1

        # Immediate retry: entry NOT picked up (backoff not expired)
        processed = await processor.process_pending()
        assert processed == 0
        assert entry.retry_count == 1  # unchanged

        # Simulate time passing (backoff expired)
        entry._next_retry_at = datetime.now(UTC) - timedelta(seconds=1)

        # Retry now succeeds
        processed = await processor.process_pending()
        assert processed == 1
        assert entry.status == OutboxEntryStatus.PROCESSED

        # Verify read model has the projected data
        query_handler = GetAvailableMenuItemsHandler(menu_item_read_repo)
        result = await query_handler.handle(GetAvailableMenuItemsQuery())
        assert len(result) == 1
        assert result[0].menu_item_id == "m-1"
        assert result[0].name == "Burger"


class TestEventualConsistency:
    """Demonstrates that queries return nothing before outbox processes."""

    async def test_query_returns_nothing_before_projection(
        self, stores, order_read_repo, menu_item_read_repo, id_generator
    ):
        # Create a menu item (writes to write DB + outbox)
        handler = CreateMenuItemHandler(_uow(stores), id_generator)
        await handler.handle(
            CreateMenuItemCommand(
                menu_item_id="m-1", name="Burger", price=Decimal("9.99")
            )
        )

        # Write side has the menu item
        assert "m-1" in stores["menu_items"]

        # Read side does NOT have it yet (eventual consistency)
        query_handler = GetAvailableMenuItemsHandler(menu_item_read_repo)
        result = await query_handler.handle(GetAvailableMenuItemsQuery())
        assert result == []

        # Outbox has the pending event
        assert len(stores["outbox"]) == 1
        assert stores["outbox"][0].event_type == "MenuItemCreated"
