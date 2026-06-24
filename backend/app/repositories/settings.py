"""Persistence access for Setting — bespoke because of the (scope, key) key."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting


class SqlAlchemySettingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, scope: str, key: str) -> Setting | None:
        return await self._session.get(Setting, {"scope": scope, "key": key})

    async def list(self, scope: str | None = None) -> list[Setting]:
        stmt = select(Setting).order_by(Setting.scope, Setting.key)
        if scope is not None:
            stmt = stmt.where(Setting.scope == scope)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(self, scope: str, key: str, value: Any) -> Setting:
        setting = await self.get(scope, key)
        if setting is None:
            setting = Setting(scope=scope, key=key, value=value)
            self._session.add(setting)
        else:
            setting.value = value
        await self._session.flush()
        return setting

    async def delete(self, setting: Setting) -> None:
        await self._session.delete(setting)
        await self._session.flush()
