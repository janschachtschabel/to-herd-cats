"""Business logic for the LLMConnection entity.

NOTE: this mirrors AgentService closely; once a third CRUD service exists the
common create/get/list/update/delete shape will be extracted into a generic
CrudService base (deferred until there are concrete cases to extract from).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_connection import LLMConnection
from app.repositories.llm_connections import SqlAlchemyLLMConnectionRepository
from app.schemas.llm_connection import LLMConnectionCreate, LLMConnectionUpdate


class LLMConnectionNotFoundError(Exception):
    """Raised when an LLM connection id does not exist."""


class LLMConnectionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SqlAlchemyLLMConnectionRepository(session)

    async def create(self, payload: LLMConnectionCreate) -> LLMConnection:
        entity = LLMConnection(**payload.model_dump(mode="json"))
        await self._repo.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def get(self, entity_id: str) -> LLMConnection:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise LLMConnectionNotFoundError(entity_id)
        return entity

    async def list(self) -> list[LLMConnection]:
        return await self._repo.list()

    async def update(
        self, entity_id: str, payload: LLMConnectionUpdate
    ) -> LLMConnection:
        entity = await self.get(entity_id)
        for field, value in payload.model_dump(mode="json", exclude_unset=True).items():
            setattr(entity, field, value)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: str) -> None:
        entity = await self.get(entity_id)
        await self._repo.delete(entity)
        await self._session.commit()
