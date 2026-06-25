"""Persistence access for MemoryRecord, with an agent-scoped recency query."""

from sqlalchemy import select

from app.models.memory import MemoryRecord
from app.repositories.base import BaseRepository


class SqlAlchemyMemoryRepository(BaseRepository[MemoryRecord]):
    model = MemoryRecord

    async def for_agent(self, agent_id: str) -> list[MemoryRecord]:
        """Return the agent's memories, most recent first (recency for recall)."""
        result = await self._session.execute(
            select(MemoryRecord)
            .where(MemoryRecord.agent_id == agent_id)
            .order_by(MemoryRecord.created_at.desc())
        )
        return list(result.scalars().all())
