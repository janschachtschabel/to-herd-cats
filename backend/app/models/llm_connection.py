"""ORM model for an LLM connection (provider, credentials ref, limits)."""

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import UuidAuditMixin


class LLMConnection(UuidAuditMixin, Base):
    __tablename__ = "llm_connections"

    name: Mapped[str] = mapped_column(String(200))
    # LiteLLM provider string, e.g. "anthropic/claude-...", "ollama/llama3".
    provider_model: Mapped[str] = mapped_column(String(200))
    api_base: Mapped[str | None] = mapped_column(String(500), default=None)
    # A SecretRef (e.g. "env:OPENAI_API_KEY"), never the plaintext key.
    api_key_ref: Mapped[str | None] = mapped_column(String(200), default=None)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    limits: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
