"""Tests for MenuItem aggregate."""

from decimal import Decimal

import pytest

from tabb.domain.events.events import MenuItemAvailable, MenuItemSoldOut
from tabb.domain.exceptions.validation import InvalidFieldTypeError, RequiredFieldError
from tabb.domain.models.menu_item import MenuItem, MenuItemId
from tabb.domain.models.value_objects import Money


class TestMenuItemFactory:
    def test_create_available_menu_item(self) -> None:
        item = MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))

        assert item.id == MenuItemId("m-1")
        assert item.name == "Burger"
        assert item.price == Money(Decimal("9.99"))
        assert item.available is True

    def test_create_records_no_events(self) -> None:
        item = MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))
        assert item.collect_events() == []


class TestMenuItemValidation:
    def test_blank_name_raises(self) -> None:
        with pytest.raises(RequiredFieldError):
            MenuItem.create(MenuItemId("m-1"), "", Money(Decimal("1")))

    def test_whitespace_name_raises(self) -> None:
        with pytest.raises(RequiredFieldError):
            MenuItem.create(MenuItemId("m-1"), "   ", Money(Decimal("1")))

    def test_wrong_id_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            MenuItem(_id="not-an-id", _name="X", _price=Money(Decimal("1")))

    def test_wrong_price_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            MenuItem.create(MenuItemId("m-1"), "Burger", "9.99")

    def test_wrong_available_type_raises(self) -> None:
        with pytest.raises(InvalidFieldTypeError):
            MenuItem(
                _id=MenuItemId("m-1"),
                _name="Burger",
                _price=Money(Decimal("1")),
                _available="yes",
            )


class TestMenuItemMarkSoldOut:
    def test_mark_sold_out(self) -> None:
        item = MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))
        item.mark_sold_out()

        assert item.available is False
        events = item.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], MenuItemSoldOut)
        assert events[0].menu_item_id == "m-1"

    def test_mark_sold_out_idempotent(self) -> None:
        item = MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))
        item.mark_sold_out()
        item.collect_events()

        item.mark_sold_out()
        assert item.collect_events() == []


class TestMenuItemMarkAvailable:
    def test_mark_available(self) -> None:
        item = MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))
        item.mark_sold_out()
        item.collect_events()

        item.mark_available()
        assert item.available is True
        events = item.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], MenuItemAvailable)
        assert events[0].menu_item_id == "m-1"

    def test_mark_available_idempotent(self) -> None:
        item = MenuItem.create(MenuItemId("m-1"), "Burger", Money(Decimal("9.99")))
        item.mark_available()
        assert item.collect_events() == []
