"""Pydantic schemas for the LLMConnection entity.

``api_key_ref`` is validated as a SecretRef so a plaintext key can never be
accepted (and therefore never persisted). See app.core.secret_ref.
"""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.core.secret_ref import is_secret_ref


def _validate_secret_ref(value: str | None) -> str | None:
    if value is not None and not is_secret_ref(value):
        raise ValueError(
            "must be a secret reference like 'env:VAR_NAME', not a plaintext secret"
        )
    return value


SecretRefField = Annotated[str | None, AfterValidator(_validate_secret_ref)]


class LLMParams(BaseModel):
    temperature: float | None = None
    max_tokens: int | None = None


class LLMLimits(BaseModel):
    cost: float | None = None  # budget ceiling
    rate: int | None = None  # requests per minute


class LLMConnectionBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    provider_model: str = Field(min_length=1, max_length=200)
    api_base: str | None = None
    api_key_ref: SecretRefField = None
    params: LLMParams = Field(default_factory=LLMParams)
    limits: LLMLimits = Field(default_factory=LLMLimits)
    enabled: bool = True


class LLMConnectionCreate(LLMConnectionBase):
    """Payload to create an LLM connection."""


class LLMConnectionUpdate(BaseModel):
    """Partial update: every field optional; unset fields are left untouched."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    provider_model: str | None = Field(default=None, min_length=1, max_length=200)
    api_base: str | None = None
    api_key_ref: SecretRefField = None
    params: LLMParams | None = None
    limits: LLMLimits | None = None
    enabled: bool | None = None


class LLMConnectionRead(LLMConnectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
