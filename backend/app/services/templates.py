"""Business logic for the Template entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template
from app.repositories.templates import SqlAlchemyTemplateRepository
from app.services.base import CrudService


class TemplateService(CrudService[Template]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyTemplateRepository(session))
