"""Pydantic schemas for the Setting entity (scoped key/value)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, JsonValue


class SettingScope(StrEnum):
    global_ = "global"
    user = "user"
    agent = "agent"


class SettingWrite(BaseModel):
    """Body for an upsert; value is any JSON. Secrets belong in a SecretRef."""

    value: JsonValue = None


class SettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scope: SettingScope
    key: str
    value: JsonValue
    created_at: datetime
    updated_at: datetime
