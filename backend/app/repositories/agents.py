"""Persistence access for Agent, behind a small interface.

Only generic SQLAlchemy is used here, so the same code runs on SQLite and
PostgreSQL. Services depend on the ``AgentRepository`` protocol, not the
concrete implementation.
"""

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent


class AgentRepository(Protocol):
    async def add(self, agent: Agent) -> Agent: ...
    async def get(self, agent_id: str) -> Agent | None: ...
    async def list(self) -> list[Agent]: ...
    async def delete(self, agent: Agent) -> None: ...


class SqlAlchemyAgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, agent: Agent) -> Agent:
        self._session.add(agent)
        await self._session.flush()
        return agent

    async def get(self, agent_id: str) -> Agent | None:
        return await self._session.get(Agent, agent_id)

    async def list(self) -> list[Agent]:
        result = await self._session.execute(select(Agent).order_by(Agent.created_at))
        return list(result.scalars().all())

    async def delete(self, agent: Agent) -> None:
        await self._session.delete(agent)
        await self._session.flush()
