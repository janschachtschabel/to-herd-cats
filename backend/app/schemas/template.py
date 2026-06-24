"""Pydantic schemas for the output Template entity."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TemplateKind(StrEnum):
    report = "report"
    research = "research"
    comparison = "comparison"


class TemplateFormat(StrEnum):
    markdown = "markdown"
    html = "html"
    pdf = "pdf"
    docx = "docx"


class TemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: TemplateKind
    output_schema: dict = Field(default_factory=dict)
    render_template: str = ""
    format: TemplateFormat = TemplateFormat.markdown
    compare_config: dict = Field(default_factory=dict)


class TemplateCreate(TemplateBase):
    """Payload to create an output template."""


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: TemplateKind | None = None
    output_schema: dict | None = None
    render_template: str | None = None
    format: TemplateFormat | None = None
    compare_config: dict | None = None


class TemplateRead(TemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
