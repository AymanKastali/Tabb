"""Domain exceptions for tabb."""

from tabb.domain.exceptions.base import DomainError
from tabb.domain.exceptions.business import (
    EmptyOrderError,
    InvalidOrderItemStateError,
    MenuItemNotAvailableError,
    OrderItemNotFoundError,
    OrderNotFullyReadyError,
    OrderNotOpenError,
)
from tabb.domain.exceptions.validation import (
    InvalidFieldTypeError,
    InvalidQuantityError,
    InvalidTableNumberError,
    NegativeMoneyError,
    RequiredFieldError,
    ValidationError,
)

__all__ = [
    "DomainError",
    "EmptyOrderError",
    "InvalidFieldTypeError",
    "InvalidOrderItemStateError",
    "InvalidQuantityError",
    "InvalidTableNumberError",
    "MenuItemNotAvailableError",
    "NegativeMoneyError",
    "OrderItemNotFoundError",
    "OrderNotFullyReadyError",
    "OrderNotOpenError",
    "RequiredFieldError",
    "ValidationError",
]
