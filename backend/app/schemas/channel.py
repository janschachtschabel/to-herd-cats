"""Pydantic schemas for the Channel entity."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import SecretRefField


class ChannelKind(StrEnum):
    slack = "slack"
    email = "email"
    matrix = "matrix"
    webhook = "webhook"


class ChannelDirection(StrEnum):
    inbound = "in"
    outbound = "out"
    both = "both"


class ChannelBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: ChannelKind
    mcp_server_id: str | None = None
    connection_ref: SecretRefField = None
    direction: ChannelDirection = ChannelDirection.outbound
    routing: list[str] = Field(default_factory=list)  # InboxItem types routed here
    enabled: bool = True


class ChannelCreate(ChannelBase):
    """Payload to register a channel."""


class ChannelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: ChannelKind | None = None
    mcp_server_id: str | None = None
    connection_ref: SecretRefField = None
    direction: ChannelDirection | None = None
    routing: list[str] | None = None
    enabled: bool | None = None


class ChannelRead(ChannelBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
