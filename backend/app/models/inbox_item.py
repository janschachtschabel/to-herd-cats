"""ORM model for an InboxItem — the postbox entry an agent posts for a human."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class InboxItem(UuidAuditMixin, Base):
    __tablename__ = "inbox_items"

    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(20))  # approval_request|question|notification|result
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    allowed_responses: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|answered|expired
    response: Mapped[dict | None] = mapped_column(JSON, default=None)
    responded_by: Mapped[str | None] = mapped_column(String(200), default=None)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    channel_ids: Mapped[list] = mapped_column(JSON, default=list)
