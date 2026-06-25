"""Pydantic schemas for publishing events to event-mode triggers."""

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    source: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


class EventDispatchResult(BaseModel):
    fired: int
    run_ids: list[str]
