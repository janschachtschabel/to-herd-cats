"""ORM model for the Skill entity — packaged know-how (SKILL.md + optional scripts).

A Skill is procedural know-how an agent follows, invoked either by the model
(matched on ``description``, progressive disclosure) or by a fixed command
(deterministic). Bundled scripts are stored as metadata here; executing them is
the sandboxed M4b milestone, not this one.
"""

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class Skill(UuidAuditMixin, Base):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(200))
    # The match/trigger signal used for progressive disclosure.
    description: Mapped[str] = mapped_column(Text)
    instructions: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(16), default="inline")
    source_ref: Mapped[str | None] = mapped_column(String(500), default=None)
    resources: Mapped[list] = mapped_column(JSON, default=list)
    commands: Mapped[list] = mapped_column(JSON, default=list)
    invocation: Mapped[str] = mapped_column(String(16), default="model_invoked")
    allowed_tool_ids: Mapped[list] = mapped_column(JSON, default=list)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    scopes: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
