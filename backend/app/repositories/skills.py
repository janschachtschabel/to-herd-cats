"""Persistence access for Skill (generic CRUD from BaseRepository)."""

from app.models.skill import Skill
from app.repositories.base import BaseRepository


class SqlAlchemySkillRepository(BaseRepository[Skill]):
    model = Skill
