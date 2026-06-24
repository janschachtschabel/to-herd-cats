"""Business logic for the Agent entity.

The service owns the unit of work (commit) and translates schemas to/from the
ORM model. It raises domain errors; the router maps them to HTTP responses.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.repositories.agents import SqlAlchemyAgentRepository
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentNotFoundError(Exception):
    """Raised when an agent id does not exist."""


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SqlAlchemyAgentRepository(session)

    async def create(self, payload: AgentCreate) -> Agent:
        agent = Agent(**payload.model_dump(mode="json"))
        await self._repo.add(agent)
        await self._session.commit()
        await self._session.refresh(agent)
        return agent

    async def get(self, agent_id: str) -> Agent:
        agent = await self._repo.get(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)
        return agent

    async def list(self) -> list[Agent]:
        return await self._repo.list()

    async def update(self, agent_id: str, payload: AgentUpdate) -> Agent:
        agent = await self.get(agent_id)
        changes = payload.model_dump(mode="json", exclude_unset=True)
        for field, value in changes.items():
            setattr(agent, field, value)
        await self._session.commit()
        await self._session.refresh(agent)
        return agent

    async def delete(self, agent_id: str) -> None:
        agent = await self.get(agent_id)
        await self._repo.delete(agent)
        await self._session.commit()
