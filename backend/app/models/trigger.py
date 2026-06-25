"""ORM model for a Trigger — how/when an agent runs (on_demand/scheduled/...)."""

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class Trigger(UuidAuditMixin, Base):
    __tablename__ = "triggers"

    # A trigger belongs to one agent; remove it when the agent is removed.
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"))
    mode: Mapped[str] = mapped_column(String(16))  # on_demand|scheduled|event|autonomous
    cron: Mapped[str | None] = mapped_column(String(100), default=None)
    timezone: Mapped[str | None] = mapped_column(String(64), default=None)
    event_source: Mapped[str | None] = mapped_column(String(200), default=None)
    event_filter: Mapped[dict] = mapped_column(JSON, default=dict)
    # {interval, stop_condition, budget} for the autonomous loop mode.
    loop_config: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
