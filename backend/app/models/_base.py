"""Shared ORM building blocks: a UUID primary key + audit-timestamp mixin.

Every domain entity carries the same id and created_at/updated_at columns, so
they live here once instead of being repeated per model.
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


def uuid_str() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class UuidAuditMixin:
    """String UUID primary key plus created_at / updated_at audit columns."""

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
