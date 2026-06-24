"""Business logic for the Channel entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.repositories.channels import SqlAlchemyChannelRepository
from app.services.base import CrudService


class ChannelService(CrudService[Channel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyChannelRepository(session))
