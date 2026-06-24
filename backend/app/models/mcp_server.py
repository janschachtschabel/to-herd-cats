"""ORM model for an MCP server registration (the gateway's tool/data source)."""

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class MCPServer(UuidAuditMixin, Base):
    __tablename__ = "mcp_servers"

    name: Mapped[str] = mapped_column(String(200))
    transport: Mapped[str] = mapped_column(String(20))  # stdio | streamable_http
    url: Mapped[str | None] = mapped_column(String(500), default=None)
    command: Mapped[str | None] = mapped_column(String(500), default=None)
    args: Mapped[list] = mapped_column(JSON, default=list)
    # Smithery-style config schema rendered by the generic "add server" form.
    config_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    credentials_ref: Mapped[str | None] = mapped_column(String(200), default=None)
    status: Mapped[str] = mapped_column(String(20), default="unknown")
    discovered_tools: Mapped[list] = mapped_column(JSON, default=list)
