"""Pydantic schemas for the Run entity."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RunStatus(StrEnum):
    queued = "queued"
    running = "running"
    waiting_human = "waiting_human"
    completed = "completed"
    failed = "failed"


class RunInput(BaseModel):
    goal: str = Field(min_length=1)
    documents: list[str] = Field(default_factory=list)
    params: dict = Field(default_factory=dict)


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    trigger_id: str | None
    status: RunStatus
    input: dict
    thread_id: str | None
    result: dict
    rendered_outputs: list
    metrics: dict
    trace_id: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
