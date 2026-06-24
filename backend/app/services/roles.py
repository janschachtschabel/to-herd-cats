"""Business logic for the Role entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.repositories.roles import SqlAlchemyRoleRepository
from app.services.base import CrudService


class RoleService(CrudService[Role]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyRoleRepository(session))
