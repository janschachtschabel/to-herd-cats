"""Read access to the postbox (InboxItem). Responding lives in RunService."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inbox_item import InboxItem
from app.repositories.inbox_items import SqlAlchemyInboxItemRepository
from app.services.base import EntityNotFoundError


class InboxService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqlAlchemyInboxItemRepository(session)

    async def get(self, item_id: str) -> InboxItem:
        item = await self._repo.get(item_id)
        if item is None:
            raise EntityNotFoundError(item_id)
        return item

    async def list(self) -> list[InboxItem]:
        return await self._repo.list()
