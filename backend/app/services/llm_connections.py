"""Business logic for the LLMConnection entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_connection import LLMConnection
from app.repositories.llm_connections import SqlAlchemyLLMConnectionRepository
from app.services.base import CrudService


class LLMConnectionService(CrudService[LLMConnection]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyLLMConnectionRepository(session))
