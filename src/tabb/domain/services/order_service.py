"""Domain service for cross-aggregate order validation."""

from tabb.domain.exceptions.business import MenuItemNotAvailableError
from tabb.domain.models.menu_item import MenuItem, MenuItemId


class OrderDomainService:
    """Handles business rules that span multiple aggregates."""

    @staticmethod
    def verify_items_available(
        requested_ids: list[MenuItemId],
        menu_items: list[MenuItem],
    ) -> None:
        """Verify that all requested menu items are available.

        Args:
            requested_ids: The menu item IDs the customer wants to order.
            menu_items: The resolved MenuItem aggregates.

        Raises:
            MenuItemNotAvailableError: If any requested items are sold out or missing.
        """
        available_ids = {item.id for item in menu_items if item.available}
        unavailable = [
            str(mid) for mid in requested_ids if mid not in available_ids
        ]
        if unavailable:
            raise MenuItemNotAvailableError(unavailable)
