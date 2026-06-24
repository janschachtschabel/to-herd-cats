"""Business logic for the Agent entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.repositories.agents import SqlAlchemyAgentRepository
from app.services.base import CrudService


class AgentService(CrudService[Agent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyAgentRepository(session))
