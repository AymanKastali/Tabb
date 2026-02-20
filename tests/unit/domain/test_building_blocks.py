"""Tests for domain building blocks (Id, Entity, AggregateRoot)."""

from dataclasses import dataclass

import pytest

from tabb.domain.events.base import DomainEvent
from tabb.domain.exceptions import RequiredFieldError
from tabb.domain.shared.building_blocks import AggregateRoot, Entity, Id


class TestId:
    def test_valid_string_id(self) -> None:
        i = Id[str]("abc")
        assert i.value == "abc"
        assert str(i) == "abc"

    def test_valid_int_id(self) -> None:
        i = Id[int](42)
        assert i.value == 42

    def test_none_raises(self) -> None:
        with pytest.raises(RequiredFieldError):
            Id[str](None)

    def test_blank_string_raises(self) -> None:
        with pytest.raises(RequiredFieldError):
            Id[str]("   ")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(RequiredFieldError):
            Id[str]("")

    def test_equality_same_type(self) -> None:
        assert Id[str]("a") == Id[str]("a")
        assert Id[str]("a") != Id[str]("b")

    def test_equality_different_subclass(self) -> None:
        class FooId(Id[str]): ...

        class BarId(Id[str]): ...

        assert FooId("a") != BarId("a")

    def test_hash(self) -> None:
        assert hash(Id[str]("a")) == hash(Id[str]("a"))

    def test_bool(self) -> None:
        assert bool(Id[str]("a")) is True
        assert bool(Id[int](1)) is True

    def test_repr(self) -> None:
        assert repr(Id[str]("x")) == "Id('x')"

    def test_immutable(self) -> None:
        i = Id[str]("a")
        with pytest.raises(AttributeError):
            i.value = "b"


class TestEntity:
    def test_identity_equality(self) -> None:
        @dataclass(eq=False)
        class Foo(Entity[Id[str]]):
            _name: str

        a = Foo(_id=Id[str]("1"), _name="A")
        b = Foo(_id=Id[str]("1"), _name="B")
        assert a == b

    def test_identity_inequality(self) -> None:
        @dataclass(eq=False)
        class Foo(Entity[Id[str]]):
            _name: str

        a = Foo(_id=Id[str]("1"), _name="A")
        b = Foo(_id=Id[str]("2"), _name="A")
        assert a != b

    def test_id_property(self) -> None:
        @dataclass
        class Foo(Entity[Id[str]]):
            pass

        f = Foo(_id=Id[str]("1"))
        assert f.id == Id[str]("1")

    def test_hash(self) -> None:
        @dataclass(eq=False)
        class Foo(Entity[Id[str]]):
            pass

        a = Foo(_id=Id[str]("1"))
        b = Foo(_id=Id[str]("1"))
        assert hash(a) == hash(b)


class TestAggregateRoot:
    @dataclass(frozen=True, kw_only=True)
    class SomeEvent(DomainEvent):
        data: str

    def test_record_and_collect_events(self) -> None:
        @dataclass
        class Foo(AggregateRoot[Id[str]]):
            pass

        foo = Foo(_id=Id[str]("1"))
        event = self.SomeEvent(data="test")
        foo._record_event(event)

        events = foo.collect_events()
        assert len(events) == 1
        assert events[0] == event

    def test_collect_clears_events(self) -> None:
        @dataclass
        class Foo(AggregateRoot[Id[str]]):
            pass

        foo = Foo(_id=Id[str]("1"))
        foo._record_event(self.SomeEvent(data="a"))
        foo.collect_events()

        assert foo.collect_events() == []

    def test_multiple_events(self) -> None:
        @dataclass
        class Foo(AggregateRoot[Id[str]]):
            pass

        foo = Foo(_id=Id[str]("1"))
        foo._record_event(self.SomeEvent(data="a"))
        foo._record_event(self.SomeEvent(data="b"))

        events = foo.collect_events()
        assert len(events) == 2
