"""Business logic for the Tool entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import Tool
from app.repositories.tools import SqlAlchemyToolRepository
from app.services.base import CrudService


class ToolService(CrudService[Tool]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyToolRepository(session))
