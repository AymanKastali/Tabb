"""Tests for domain value objects."""

from decimal import Decimal

import pytest

from tabb.domain.exceptions.validation import (
    InvalidFieldTypeError,
    InvalidQuantityError,
    InvalidTableNumberError,
    NegativeMoneyError,
)
from tabb.domain.models.value_objects import Money, Quantity, TableNumber


class TestTableNumber:
    def test_valid_table_number(self) -> None:
        t = TableNumber(1)
        assert t.value == 1

    def test_zero_raises(self) -> None:
        with pytest.raises(InvalidTableNumberError):
            TableNumber(0)

    def test_negative_raises(self) -> None:
        with pytest.raises(InvalidTableNumberError):
            TableNumber(-5)

    def test_non_int_raises(self) -> None:
        with pytest.raises(InvalidTableNumberError):
            TableNumber("3")

    def test_immutable(self) -> None:
        t = TableNumber(1)
        with pytest.raises(AttributeError):
            t.value = 2

    def test_equality(self) -> None:
        assert TableNumber(1) == TableNumber(1)
        assert TableNumber(1) != TableNumber(2)


class TestMoney:
    def test_valid_money(self) -> None:
        m = Money(Decimal("9.99"))
        assert m.amount == Decimal("9.99")

    def test_zero_is_valid(self) -> None:
        m = Money(Decimal("0"))
        assert m.amount == Decimal("0")

    def test_negative_raises(self) -> None:
        with pytest.raises(NegativeMoneyError):
            Money(Decimal("-1"))

    def test_non_decimal_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            Money(10.0)

    def test_add(self) -> None:
        result = Money(Decimal("5")) + Money(Decimal("3"))
        assert result == Money(Decimal("8"))

    def test_add_non_money_returns_not_implemented(self) -> None:
        assert Money(Decimal("5")).__add__(10) is NotImplemented

    def test_multiply(self) -> None:
        result = Money(Decimal("5")) * 3
        assert result == Money(Decimal("15"))

    def test_immutable(self) -> None:
        m = Money(Decimal("1"))
        with pytest.raises(AttributeError):
            m.amount = Decimal("2")

    def test_equality(self) -> None:
        assert Money(Decimal("1")) == Money(Decimal("1"))
        assert Money(Decimal("1")) != Money(Decimal("2"))


class TestQuantity:
    def test_valid_quantity(self) -> None:
        q = Quantity(3)
        assert q.value == 3

    def test_zero_raises(self) -> None:
        with pytest.raises(InvalidQuantityError):
            Quantity(0)

    def test_negative_raises(self) -> None:
        with pytest.raises(InvalidQuantityError):
            Quantity(-1)

    def test_non_int_raises(self) -> None:
        with pytest.raises(InvalidQuantityError):
            Quantity(1.5)

    def test_immutable(self) -> None:
        q = Quantity(1)
        with pytest.raises(AttributeError):
            q.value = 2

    def test_equality(self) -> None:
        assert Quantity(1) == Quantity(1)
        assert Quantity(1) != Quantity(2)
