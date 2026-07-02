"""Pydantic schemas for the current-principal (auth) endpoint."""

from pydantic import BaseModel


class PrincipalRead(BaseModel):
    """The calling identity and its permissions, for the frontend to gate on."""

    subject: str
    permissions: list[str]


class PermissionOption(BaseModel):
    """A selectable permission for the role editor (id == name == the string)."""

    id: str
    name: str
