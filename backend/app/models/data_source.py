"""ORM model for a DataSource (vector / graph / relational / document / wiki)."""

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class DataSource(UuidAuditMixin, Base):
    __tablename__ = "data_sources"

    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20))  # vector|graph|relational|document|wiki
    # Either exposed via an MCP server, or a direct driver connection.
    mcp_server_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("mcp_servers.id", ondelete="SET NULL"), default=None
    )
    connection_ref: Mapped[dict] = mapped_column(JSON, default=dict)  # {driver, dsn_ref}
    capabilities: Mapped[list] = mapped_column(JSON, default=list)  # read|write|search
    embedding_model: Mapped[str | None] = mapped_column(String(200), default=None)
    dimension: Mapped[int | None] = mapped_column(Integer, default=None)
    collection: Mapped[str | None] = mapped_column(String(200), default=None)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
