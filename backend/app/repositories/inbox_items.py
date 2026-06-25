"""Persistence access for InboxItem (generic CRUD from BaseRepository)."""

from app.models.inbox_item import InboxItem
from app.repositories.base import BaseRepository


class SqlAlchemyInboxItemRepository(BaseRepository[InboxItem]):
    model = InboxItem
