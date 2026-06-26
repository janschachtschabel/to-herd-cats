"""Business logic for the Role entity (generic CRUD plus authz resolution)."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.repositories.roles import SqlAlchemyRoleRepository
from app.services.base import CrudService

logger = logging.getLogger(__name__)


class RoleService(CrudService[Role]):
    def __init__(self, session: AsyncSession) -> None:
        repo = SqlAlchemyRoleRepository(session)
        super().__init__(session, repo)
        self._roles = repo

    async def permissions_for_roles(self, names: list[str]) -> set[str]:
        """Union of permissions across the named roles (unknown names ignored)."""
        roles = await self._roles.by_names(names)
        missing = set(names) - {role.name for role in roles}
        if missing:
            logger.warning("authz: unknown role names ignored: %s", sorted(missing))
        return {permission for role in roles for permission in role.permissions}
