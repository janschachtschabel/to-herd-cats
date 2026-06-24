"""Persistence access for Role (generic CRUD from BaseRepository)."""

from app.models.role import Role
from app.repositories.base import BaseRepository


class SqlAlchemyRoleRepository(BaseRepository[Role]):
    model = Role
