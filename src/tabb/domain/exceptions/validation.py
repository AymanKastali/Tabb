"""Validation exceptions for tabb."""

from tabb.domain.exceptions.base import DomainError


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    code = "VALIDATION_ERROR"


class RequiredFieldError(ValidationError):
    """Raised when a required field is missing or blank."""

    code = "REQUIRED_FIELD"

    def __init__(self, class_name: str, field_name: str) -> None:
        super().__init__(f"{class_name}.{field_name} is required and cannot be None or blank")
        self.class_name = class_name
        self.field_name = field_name


class InvalidFieldTypeError(ValidationError):
    """Raised when a field receives a value of the wrong type."""

    code = "INVALID_FIELD_TYPE"

    def __init__(self, class_name: str, field_name: str, expected_type: str) -> None:
        super().__init__(
            f"{class_name}.{field_name} must be of type {expected_type}"
        )
        self.class_name = class_name
        self.field_name = field_name
        self.expected_type = expected_type


class InvalidTableNumberError(ValidationError):
    """Raised when a table number is not a positive integer."""

    code = "INVALID_TABLE_NUMBER"

    def __init__(self, value: object) -> None:
        super().__init__(f"Table number must be a positive integer, got {value!r}")
        self.value = value


class NegativeMoneyError(ValidationError):
    """Raised when a monetary amount is negative."""

    code = "NEGATIVE_MONEY"

    def __init__(self, amount: object) -> None:
        super().__init__(f"Money amount cannot be negative, got {amount!r}")
        self.amount = amount


class InvalidQuantityError(ValidationError):
    """Raised when a quantity is not a positive integer."""

    code = "INVALID_QUANTITY"

    def __init__(self, value: object) -> None:
        super().__init__(f"Quantity must be a positive integer, got {value!r}")
        self.value = value
