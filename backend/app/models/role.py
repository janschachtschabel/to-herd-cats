"""ORM model for a Role (a named set of permissions; membership via Keycloak)."""

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class Role(UuidAuditMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    # e.g. ["agent.create", "tool.manage", "run.approve"].
    permissions: Mapped[list] = mapped_column(JSON, default=list)
