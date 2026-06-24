"""Business logic for the Skill entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.repositories.skills import SqlAlchemySkillRepository
from app.services.base import CrudService


class SkillService(CrudService[Skill]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemySkillRepository(session))
