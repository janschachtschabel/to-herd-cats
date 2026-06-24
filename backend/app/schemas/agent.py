"""Pydantic schemas for the Agent entity (separate from the ORM model)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AgentStatus(StrEnum):
    draft = "draft"
    active = "active"
    disabled = "disabled"


class MemoryMode(StrEnum):
    none = "none"
    short = "short"
    long = "long"


class Memory(BaseModel):
    mode: MemoryMode = MemoryMode.none
    vector_store_ref: str | None = None


class Guardrails(BaseModel):
    requires_approval_for: list[str] = Field(default_factory=list)


class AgentBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: str = ""
    goal: str = ""
    description: str | None = None
    icon: str | None = None
    instructions: str | None = None
    llm_connection_id: str | None = None
    tool_ids: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    data_source_ids: list[str] = Field(default_factory=list)
    default_template_id: str | None = None
    memory: Memory = Field(default_factory=Memory)
    guardrails: Guardrails = Field(default_factory=Guardrails)
    status: AgentStatus = AgentStatus.draft


class AgentCreate(AgentBase):
    """Payload to create an agent (only ``name`` is required)."""


class AgentUpdate(BaseModel):
    """Partial update: every field optional; unset fields are left untouched."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = None
    goal: str | None = None
    description: str | None = None
    icon: str | None = None
    instructions: str | None = None
    llm_connection_id: str | None = None
    tool_ids: list[str] | None = None
    skill_ids: list[str] | None = None
    data_source_ids: list[str] | None = None
    default_template_id: str | None = None
    memory: Memory | None = None
    guardrails: Guardrails | None = None
    status: AgentStatus | None = None


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
