"""Generic async CRUD persistence, shared by every entity repository.

Only generic SQLAlchemy is used, so the same code runs on SQLite and
PostgreSQL. Entity repositories subclass this, set ``model``, and add
entity-specific queries as they appear.
"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def get(self, entity_id: str) -> ModelT | None:
        return await self._session.get(self.model, entity_id)

    async def list(self) -> list[ModelT]:
        result = await self._session.execute(
            select(self.model).order_by(self.model.created_at)
        )
        return list(result.scalars().all())

    async def delete(self, entity: ModelT) -> None:
        await self._session.delete(entity)
        await self._session.flush()
