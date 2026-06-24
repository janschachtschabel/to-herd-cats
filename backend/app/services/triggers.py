"""Business logic for the Trigger entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trigger import Trigger
from app.repositories.triggers import SqlAlchemyTriggerRepository
from app.services.base import CrudService


class TriggerService(CrudService[Trigger]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyTriggerRepository(session))
