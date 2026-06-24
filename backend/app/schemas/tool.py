"""Pydantic schemas for the Tool entity."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ToolType(StrEnum):
    mcp = "mcp"
    http = "http"
    builtin = "builtin"


class ToolBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    type: ToolType = ToolType.mcp
    mcp_server_id: str | None = None
    tool_name: str | None = None
    input_schema: dict = Field(default_factory=dict)
    requires_approval: bool = False
    scopes: list[str] = Field(default_factory=list)
    enabled: bool = True


class ToolCreate(ToolBase):
    """Payload to create a tool."""


class ToolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    type: ToolType | None = None
    mcp_server_id: str | None = None
    tool_name: str | None = None
    input_schema: dict | None = None
    requires_approval: bool | None = None
    scopes: list[str] | None = None
    enabled: bool | None = None


class ToolRead(ToolBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
