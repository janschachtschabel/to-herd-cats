"""ORM model for an output Template (report / research / comparison)."""

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class Template(UuidAuditMixin, Base):
    __tablename__ = "templates"

    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20))  # report|research|comparison
    output_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    render_template: Mapped[str] = mapped_column(Text, default="")  # Jinja2
    format: Mapped[str] = mapped_column(String(16), default="markdown")
    compare_config: Mapped[dict] = mapped_column(JSON, default=dict)
