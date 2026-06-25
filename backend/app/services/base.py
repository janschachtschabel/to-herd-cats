"""Generic CRUD service shared by entity services.

Holds the unit of work (commit) and the schema->ORM mapping common to every
entity. Subclasses bind a concrete repository; entity-specific logic is added
by extending or overriding methods as it appears.
"""

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base
from app.repositories.base import BaseRepository


class EntityNotFoundError(Exception):
    """Raised when an entity id does not exist."""


class CrudService[ModelT: Base]:
    def __init__(self, session: AsyncSession, repository: BaseRepository[ModelT]) -> None:
        self._session = session
        self._repo = repository

    async def create(self, payload: BaseModel) -> ModelT:
        entity = self._repo.model(**payload.model_dump(mode="json"))
        await self._repo.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def get(self, entity_id: str) -> ModelT:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise EntityNotFoundError(entity_id)
        return entity

    async def list(self) -> list[ModelT]:
        return await self._repo.list()

    async def update(self, entity_id: str, payload: BaseModel) -> ModelT:
        entity = await self.get(entity_id)
        for field, value in payload.model_dump(mode="json", exclude_unset=True).items():
            if not hasattr(entity, field):
                continue  # ignore fields not mapped on the model (schema-drift guard)
            setattr(entity, field, value)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: str) -> None:
        entity = await self.get(entity_id)
        await self._repo.delete(entity)
        await self._session.commit()
