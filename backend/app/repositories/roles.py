"""Persistence access for Role (generic CRUD plus a name lookup for authz)."""

from sqlalchemy import select

from app.models.role import Role
from app.repositories.base import BaseRepository


class SqlAlchemyRoleRepository(BaseRepository[Role]):
    model = Role

    async def by_names(self, names: list[str]) -> list[Role]:
        """Return the roles whose name is in ``names`` (empty list for no names)."""
        if not names:
            return []
        result = await self._session.execute(select(Role).where(Role.name.in_(names)))
        return list(result.scalars().all())
