"""Persistence access for DataSource (generic CRUD from BaseRepository)."""

from app.models.data_source import DataSource
from app.repositories.base import BaseRepository


class SqlAlchemyDataSourceRepository(BaseRepository[DataSource]):
    model = DataSource
