"""Persistence access for Run (generic CRUD from BaseRepository)."""

from app.models.run import Run
from app.repositories.base import BaseRepository


class SqlAlchemyRunRepository(BaseRepository[Run]):
    model = Run
