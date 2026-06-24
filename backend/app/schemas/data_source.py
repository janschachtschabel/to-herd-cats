"""Pydantic schemas for the DataSource entity."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import SecretRefField


class DataSourceKind(StrEnum):
    vector = "vector"
    graph = "graph"
    relational = "relational"
    document = "document"
    wiki = "wiki"


class DataSourceCapability(StrEnum):
    read = "read"
    write = "write"
    search = "search"


class ConnectionRef(BaseModel):
    driver: str | None = None
    dsn_ref: SecretRefField = None  # SecretRef to the DSN, never plaintext


class DataSourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: DataSourceKind
    mcp_server_id: str | None = None
    connection_ref: ConnectionRef = Field(default_factory=ConnectionRef)
    capabilities: list[DataSourceCapability] = Field(default_factory=list)
    embedding_model: str | None = None
    dimension: int | None = None
    collection: str | None = None
    enabled: bool = True


class DataSourceCreate(DataSourceBase):
    """Payload to register a data source."""


class DataSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: DataSourceKind | None = None
    mcp_server_id: str | None = None
    connection_ref: ConnectionRef | None = None
    capabilities: list[DataSourceCapability] | None = None
    embedding_model: str | None = None
    dimension: int | None = None
    collection: str | None = None
    enabled: bool | None = None


class DataSourceRead(DataSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
