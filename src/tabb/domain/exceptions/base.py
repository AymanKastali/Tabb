"""Base domain exception for tabb."""


class DomainError(Exception):
    """Base exception for all domain errors."""

    code = "DOMAIN_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
