"""Tests for domain exceptions."""

from tabb.domain.exceptions import (
    DomainError,
    EmptyOrderError,
    InvalidFieldTypeError,
    InvalidOrderItemStateError,
    InvalidQuantityError,
    InvalidTableNumberError,
    MenuItemNotAvailableError,
    NegativeMoneyError,
    OrderItemNotFoundError,
    OrderNotFullyReadyError,
    OrderNotOpenError,
    RequiredFieldError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_validation_error_is_domain_error(self) -> None:
        assert issubclass(ValidationError, DomainError)

    def test_required_field_is_validation_error(self) -> None:
        assert issubclass(RequiredFieldError, ValidationError)

    def test_invalid_field_type_is_validation_error(self) -> None:
        assert issubclass(InvalidFieldTypeError, ValidationError)

    def test_invalid_table_number_is_validation_error(self) -> None:
        assert issubclass(InvalidTableNumberError, ValidationError)

    def test_negative_money_is_validation_error(self) -> None:
        assert issubclass(NegativeMoneyError, ValidationError)

    def test_invalid_quantity_is_validation_error(self) -> None:
        assert issubclass(InvalidQuantityError, ValidationError)

    def test_business_errors_are_domain_errors(self) -> None:
        assert issubclass(EmptyOrderError, DomainError)
        assert issubclass(OrderNotOpenError, DomainError)
        assert issubclass(OrderNotFullyReadyError, DomainError)
        assert issubclass(OrderItemNotFoundError, DomainError)
        assert issubclass(InvalidOrderItemStateError, DomainError)
        assert issubclass(MenuItemNotAvailableError, DomainError)


class TestExceptionCodes:
    def test_empty_order_error(self) -> None:
        e = EmptyOrderError()
        assert e.code == "EMPTY_ORDER"

    def test_order_not_open_error(self) -> None:
        e = OrderNotOpenError("o-1", "completed")
        assert e.code == "ORDER_NOT_OPEN"
        assert e.order_id == "o-1"
        assert e.status == "completed"

    def test_order_not_fully_ready_error(self) -> None:
        e = OrderNotFullyReadyError("o-1")
        assert e.code == "ORDER_NOT_FULLY_READY"
        assert e.order_id == "o-1"

    def test_order_item_not_found_error(self) -> None:
        e = OrderItemNotFoundError("o-1", "oi-1")
        assert e.code == "ORDER_ITEM_NOT_FOUND"
        assert e.order_id == "o-1"
        assert e.item_id == "oi-1"

    def test_invalid_order_item_state_error(self) -> None:
        e = InvalidOrderItemStateError("oi-1", "ready", "cancel")
        assert e.code == "INVALID_ORDER_ITEM_STATE"
        assert e.item_id == "oi-1"
        assert e.current_status == "ready"
        assert e.action == "cancel"

    def test_menu_item_not_available_error(self) -> None:
        e = MenuItemNotAvailableError(["m-1", "m-2"])
        assert e.code == "MENU_ITEM_NOT_AVAILABLE"
        assert e.menu_item_ids == ["m-1", "m-2"]

    def test_required_field_error(self) -> None:
        e = RequiredFieldError("Order", "name")
        assert e.code == "REQUIRED_FIELD"
        assert e.class_name == "Order"
        assert e.field_name == "name"

    def test_invalid_field_type_error(self) -> None:
        e = InvalidFieldTypeError("Order", "table", "TableNumber")
        assert e.code == "INVALID_FIELD_TYPE"
        assert e.class_name == "Order"
        assert e.field_name == "table"
        assert e.expected_type == "TableNumber"

    def test_invalid_table_number_error(self) -> None:
        e = InvalidTableNumberError(-1)
        assert e.code == "INVALID_TABLE_NUMBER"

    def test_negative_money_error(self) -> None:
        from decimal import Decimal

        e = NegativeMoneyError(Decimal("-5"))
        assert e.code == "NEGATIVE_MONEY"

    def test_invalid_quantity_error(self) -> None:
        e = InvalidQuantityError(0)
        assert e.code == "INVALID_QUANTITY"
