"""ORM model for a MemoryRecord - a stored past interaction for later recall.

Distinct from the agent's ``memory`` *config* (the ``Memory`` Pydantic schema in
schemas/agent.py), which only selects the recall mode (none / short / long).
"""

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class MemoryRecord(UuidAuditMixin, Base):
    __tablename__ = "memories"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"))
    run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("runs.id", ondelete="SET NULL"), default=None
    )
    content: Mapped[str] = mapped_column(Text)
    # Embedding vector for long-term (semantic) recall; None for short-term.
    embedding: Mapped[list | None] = mapped_column(JSON, default=None)
