"""Pydantic schemas for the InboxItem entity (the postbox)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class InboxItemType(StrEnum):
    approval_request = "approval_request"
    question = "question"
    notification = "notification"
    result = "result"


class InboxStatus(StrEnum):
    pending = "pending"
    answered = "answered"
    expired = "expired"


class InboxResponse(BaseModel):
    """A human's reply to an InboxItem; replayed into the run's checkpoint."""

    action: str = Field(min_length=1)  # accept|edit|reject|respond|ignore
    content: JsonValue = None
    responded_by: str | None = None


class InboxItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    agent_id: str
    type: InboxItemType
    payload: dict
    allowed_responses: list
    status: InboxStatus
    response: dict | None
    responded_by: str | None
    responded_at: datetime | None
    channel_ids: list
    created_at: datetime
    updated_at: datetime
