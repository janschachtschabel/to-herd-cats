"""ORM model for a Run — one execution of an agent definition."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class Run(UuidAuditMixin, Base):
    __tablename__ = "runs"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"))
    trigger_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("triggers.id", ondelete="SET NULL"), default=None
    )
    status: Mapped[str] = mapped_column(String(16), default="queued")
    input: Mapped[dict] = mapped_column(JSON, default=dict)  # {goal, documents, params}
    thread_id: Mapped[str | None] = mapped_column(String(64), default=None)  # LangGraph (M4.2)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    rendered_outputs: Mapped[list] = mapped_column(JSON, default=list)  # Template render (M4.4)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)  # {tokens, cost, duration}
    trace_id: Mapped[str | None] = mapped_column(String(64), default=None)  # Langfuse (M6)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
