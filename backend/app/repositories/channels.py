"""Persistence access for Channel (generic CRUD from BaseRepository)."""

from app.models.channel import Channel
from app.repositories.base import BaseRepository


class SqlAlchemyChannelRepository(BaseRepository[Channel]):
    model = Channel
