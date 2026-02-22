"""Shared value objects for the domain layer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tabb.domain.exceptions.validation import (
    InvalidFieldTypeError,
    InvalidQuantityError,
    InvalidTableNumberError,
    NegativeMoneyError,
)


@dataclass(frozen=True, slots=True)
class TableNumber:
    """Value object for a restaurant table number."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise InvalidTableNumberError(self.value)
        if self.value <= 0:
            raise InvalidTableNumberError(self.value)


@dataclass(frozen=True, slots=True)
class Money:
    """Value object for monetary amounts using exact Decimal arithmetic."""

    amount: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise InvalidFieldTypeError(type(self).__name__, "amount", "Decimal")
        if self.amount < 0:
            raise NegativeMoneyError(self.amount)

    def __add__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(amount=self.amount + other.amount)

    def __mul__(self, quantity: int) -> Money:
        return Money(amount=self.amount * quantity)


@dataclass(frozen=True, slots=True)
class Quantity:
    """Value object for item quantities."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise InvalidQuantityError(self.value)
        if self.value <= 0:
            raise InvalidQuantityError(self.value)
