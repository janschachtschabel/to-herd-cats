"""Persistence access for Template (generic CRUD from BaseRepository)."""

from app.models.template import Template
from app.repositories.base import BaseRepository


class SqlAlchemyTemplateRepository(BaseRepository[Template]):
    model = Template
