"""Domain events for tabb."""

from dataclasses import dataclass

from tabb.domain.events.base import DomainEvent

# Define your domain events below. Each event should be a frozen,
# keyword-only dataclass inheriting from DomainEvent.
#
# Example:
#
# @dataclass(frozen=True, kw_only=True)
# class OrderPlaced(DomainEvent):
#     order_id: str
#     customer_id: str
