"""ORM model for the Agent entity — the cockpit's configurable 'employee'.

An Agent is a *definition* (role, goal, wiring, guardrails), not a running
process; execution lives in the runtime/run modules. Foreign keys to the other
capability entities (LLMConnection, Tool, Skill, ...) are added when those
modules land; for now the references are plain id lists/strings.
"""

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class Agent(UuidAuditMixin, Base):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(200), default="")
    goal: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str | None] = mapped_column(Text, default=None)
    icon: Mapped[str | None] = mapped_column(String(100), default=None)
    instructions: Mapped[str | None] = mapped_column(Text, default=None)

    # References to other entities (FKs follow when those tables exist).
    llm_connection_id: Mapped[str | None] = mapped_column(String(36), default=None)
    tool_ids: Mapped[list] = mapped_column(JSON, default=list)
    skill_ids: Mapped[list] = mapped_column(JSON, default=list)
    data_source_ids: Mapped[list] = mapped_column(JSON, default=list)
    default_template_id: Mapped[str | None] = mapped_column(String(36), default=None)

    memory: Mapped[dict] = mapped_column(JSON, default=dict)
    guardrails: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="draft")
