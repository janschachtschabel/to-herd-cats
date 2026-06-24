"""Pydantic schemas for the Skill entity."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SkillSource(StrEnum):
    inline = "inline"
    file = "file"
    git = "git"
    registry = "registry"


class SkillInvocation(StrEnum):
    model_invoked = "model_invoked"
    command = "command"
    both = "both"


class SkillCommand(BaseModel):
    command: str = Field(min_length=1)
    input_schema: dict | None = None


class SkillResource(BaseModel):
    path: str = Field(min_length=1)
    kind: str = "other"  # e.g. script | reference | template | other


class SkillBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)  # drives progressive disclosure
    instructions: str = ""
    source: SkillSource = SkillSource.inline
    source_ref: str | None = None
    resources: list[SkillResource] = Field(default_factory=list)
    commands: list[SkillCommand] = Field(default_factory=list)
    invocation: SkillInvocation = SkillInvocation.model_invoked
    allowed_tool_ids: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    scopes: dict = Field(default_factory=dict)
    enabled: bool = True


class SkillCreate(SkillBase):
    """Payload to create a skill."""


class SkillUpdate(BaseModel):
    """Partial update: every field optional; unset fields are left untouched."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    instructions: str | None = None
    source: SkillSource | None = None
    source_ref: str | None = None
    resources: list[SkillResource] | None = None
    commands: list[SkillCommand] | None = None
    invocation: SkillInvocation | None = None
    allowed_tool_ids: list[str] | None = None
    requires_approval: bool | None = None
    scopes: dict | None = None
    enabled: bool | None = None


class SkillRead(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
