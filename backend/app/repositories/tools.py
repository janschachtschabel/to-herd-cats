"""Persistence access for Tool (generic CRUD from BaseRepository)."""

from app.models.tool import Tool
from app.repositories.base import BaseRepository


class SqlAlchemyToolRepository(BaseRepository[Tool]):
    model = Tool
