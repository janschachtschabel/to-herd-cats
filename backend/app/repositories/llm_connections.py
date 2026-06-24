"""Persistence access for LLMConnection (generic CRUD from BaseRepository)."""

from app.models.llm_connection import LLMConnection
from app.repositories.base import BaseRepository


class SqlAlchemyLLMConnectionRepository(BaseRepository[LLMConnection]):
    model = LLMConnection
