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
