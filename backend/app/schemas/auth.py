"""Pydantic schemas for the current-principal (auth) endpoint."""

from pydantic import BaseModel


class PrincipalRead(BaseModel):
    """The calling identity and its permissions, for the frontend to gate on."""

    subject: str
    permissions: list[str]
