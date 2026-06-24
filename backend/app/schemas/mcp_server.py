"""Pydantic schemas for the MCPServer entity."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import SecretRefField


class MCPTransport(StrEnum):
    stdio = "stdio"
    streamable_http = "streamable_http"


class MCPServerBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    transport: MCPTransport
    url: str | None = None
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    config_schema: dict = Field(default_factory=dict)
    credentials_ref: SecretRefField = None


class MCPServerCreate(MCPServerBase):
    """Payload to register an MCP server."""


class MCPServerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    transport: MCPTransport | None = None
    url: str | None = None
    command: str | None = None
    args: list[str] | None = None
    config_schema: dict | None = None
    credentials_ref: SecretRefField = None


class MCPServerRead(MCPServerBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    # Server-managed fields (not set on create).
    status: str
    discovered_tools: list = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
