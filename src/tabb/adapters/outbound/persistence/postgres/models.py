"""SQLAlchemy ORM models for tabb.

These are persistence models — distinct from domain models.
They handle the mapping between database rows and the ORM layer.
Domain models live in tabb.domain.models.
"""

from uuid import uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class ExampleModel(Base):
    """Example persistence model — replace with your own."""

    __tablename__ = "examples"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
