"""ORM model for a Tool — a single callable capability (mcp/http/builtin)."""

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class Tool(UuidAuditMixin, Base):
    __tablename__ = "tools"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(String(16), default="mcp")  # mcp | http | builtin
    # An mcp tool belongs to a server; if the server is removed the link is nulled.
    mcp_server_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("mcp_servers.id", ondelete="SET NULL"), default=None
    )
    tool_name: Mapped[str | None] = mapped_column(String(200), default=None)
    input_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
