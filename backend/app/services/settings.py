"""Business logic for the Setting entity (bespoke: scoped key/value, upsert)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from app.repositories.settings import SqlAlchemySettingRepository
from app.services.base import EntityNotFoundError


class SettingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SqlAlchemySettingRepository(session)

    async def list(self, scope: str | None = None) -> list[Setting]:
        return await self._repo.list(scope)

    async def get(self, scope: str, key: str) -> Setting:
        setting = await self._repo.get(scope, key)
        if setting is None:
            raise EntityNotFoundError(f"{scope}:{key}")
        return setting

    async def upsert(self, scope: str, key: str, value: Any) -> Setting:
        setting = await self._repo.upsert(scope, key, value)
        await self._session.commit()
        await self._session.refresh(setting)
        return setting

    async def delete(self, scope: str, key: str) -> None:
        setting = await self.get(scope, key)
        await self._repo.delete(setting)
        await self._session.commit()
