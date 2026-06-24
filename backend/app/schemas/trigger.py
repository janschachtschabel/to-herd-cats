"""Pydantic schemas for the Trigger entity."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TriggerMode(StrEnum):
    on_demand = "on_demand"
    scheduled = "scheduled"
    event = "event"
    autonomous = "autonomous"


class LoopConfig(BaseModel):
    interval: int | None = None  # seconds between iterations
    stop_condition: str | None = None
    budget: dict | None = None  # e.g. {cost, tokens}


class TriggerBase(BaseModel):
    agent_id: str = Field(min_length=1)
    mode: TriggerMode
    cron: str | None = None
    timezone: str | None = None
    event_source: str | None = None
    event_filter: dict = Field(default_factory=dict)
    loop_config: LoopConfig = Field(default_factory=LoopConfig)
    enabled: bool = True


class TriggerCreate(TriggerBase):
    """Payload to create a trigger for an agent."""


class TriggerUpdate(BaseModel):
    # agent_id is intentionally not updatable: a trigger stays with its agent.
    mode: TriggerMode | None = None
    cron: str | None = None
    timezone: str | None = None
    event_source: str | None = None
    event_filter: dict | None = None
    loop_config: LoopConfig | None = None
    enabled: bool | None = None


class TriggerRead(TriggerBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
