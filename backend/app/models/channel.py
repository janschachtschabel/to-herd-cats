"""ORM model for a communication Channel (slack / email / matrix / webhook)."""

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class Channel(UuidAuditMixin, Base):
    __tablename__ = "channels"

    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20))  # slack|email|matrix|webhook
    mcp_server_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("mcp_servers.id", ondelete="SET NULL"), default=None
    )
    connection_ref: Mapped[str | None] = mapped_column(String(200), default=None)  # SecretRef
    direction: Mapped[str] = mapped_column(String(8), default="out")  # in|out|both
    routing: Mapped[list] = mapped_column(JSON, default=list)  # InboxItem types
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
