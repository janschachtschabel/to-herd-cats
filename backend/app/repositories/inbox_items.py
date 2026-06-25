"""Persistence access for InboxItem (generic CRUD + a per-run pending query)."""

from sqlalchemy import select

from app.models.inbox_item import InboxItem
from app.repositories.base import BaseRepository


class SqlAlchemyInboxItemRepository(BaseRepository[InboxItem]):
    model = InboxItem

    async def pending_for_run(self, run_id: str) -> list[InboxItem]:
        """Pending postbox items for a run (the ones a pause just posted)."""
        result = await self._session.execute(
            select(InboxItem).where(InboxItem.run_id == run_id, InboxItem.status == "pending")
        )
        return list(result.scalars().all())
