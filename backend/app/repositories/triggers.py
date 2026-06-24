"""Persistence access for Trigger (generic CRUD from BaseRepository)."""

from app.models.trigger import Trigger
from app.repositories.base import BaseRepository


class SqlAlchemyTriggerRepository(BaseRepository[Trigger]):
    model = Trigger
