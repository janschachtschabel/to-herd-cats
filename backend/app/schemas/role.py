"""Pydantic schemas for the Role entity."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    """Payload to create a role."""


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    permissions: list[str] | None = None


class RoleRead(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
