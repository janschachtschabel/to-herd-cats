"""ORM model for a Setting — a scoped key/value store (not UUID-keyed).

Unlike the other entities, a Setting is identified by its (scope, key) composite
key, so it does not use UuidAuditMixin.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import utcnow


class Setting(Base):
    __tablename__ = "settings"

    scope: Mapped[str] = mapped_column(String(16), primary_key=True)  # global|user|agent
    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
