"""Application-level exceptions for tabb."""


class ApplicationError(Exception):
    """Base exception for all application errors."""

    code = "APPLICATION_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class OrderNotFoundError(ApplicationError):
    """Raised when an order cannot be found."""

    code = "ORDER_NOT_FOUND"

    def __init__(self, order_id: str) -> None:
        super().__init__(f"Order '{order_id}' not found.")


class MenuItemNotFoundError(ApplicationError):
    """Raised when a menu item cannot be found."""

    code = "MENU_ITEM_NOT_FOUND"

    def __init__(self, menu_item_id: str) -> None:
        super().__init__(f"Menu item '{menu_item_id}' not found.")
