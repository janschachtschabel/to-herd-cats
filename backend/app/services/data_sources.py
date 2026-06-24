"""Business logic for the DataSource entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_source import DataSource
from app.repositories.data_sources import SqlAlchemyDataSourceRepository
from app.services.base import CrudService


class DataSourceService(CrudService[DataSource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyDataSourceRepository(session))
