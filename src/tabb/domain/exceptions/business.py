"""Business rule exceptions for tabb."""

from tabb.domain.exceptions.base import DomainError


class EmptyOrderError(DomainError):
    """Raised when attempting to place an order with no items."""

    code = "EMPTY_ORDER"

    def __init__(self) -> None:
        super().__init__("Order must have at least one item")


class OrderNotOpenError(DomainError):
    """Raised when attempting to modify a completed or cancelled order."""

    code = "ORDER_NOT_OPEN"

    def __init__(self, order_id: str, status: str) -> None:
        super().__init__(f"Order {order_id} is {status} and cannot be modified")
        self.order_id = order_id
        self.status = status


class OrderNotFullyReadyError(DomainError):
    """Raised when attempting to complete an order with items not yet ready."""

    code = "ORDER_NOT_FULLY_READY"

    def __init__(self, order_id: str) -> None:
        super().__init__(f"Order {order_id} has items that are not ready")
        self.order_id = order_id


class OrderItemNotFoundError(DomainError):
    """Raised when an order item cannot be found."""

    code = "ORDER_ITEM_NOT_FOUND"

    def __init__(self, order_id: str, item_id: str) -> None:
        super().__init__(f"Item {item_id} not found in order {order_id}")
        self.order_id = order_id
        self.item_id = item_id


class InvalidOrderItemStateError(DomainError):
    """Raised when an order item operation is invalid for its current state."""

    code = "INVALID_ORDER_ITEM_STATE"

    def __init__(self, item_id: str, current_status: str, action: str) -> None:
        super().__init__(f"Cannot {action} item {item_id} in status {current_status}")
        self.item_id = item_id
        self.current_status = current_status
        self.action = action


class MenuItemNotAvailableError(DomainError):
    """Raised when attempting to order a sold-out menu item."""

    code = "MENU_ITEM_NOT_AVAILABLE"

    def __init__(self, menu_item_ids: list[str]) -> None:
        items = ", ".join(menu_item_ids)
        super().__init__(f"Menu items not available: {items}")
        self.menu_item_ids = menu_item_ids
