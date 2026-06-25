"""Deliver postbox items (InboxItem) to outbound channels.

When a run pauses and posts an InboxItem, it is routed to the enabled outbound
channels whose ``routing`` matches the item's type (an empty routing accepts any
type). Delivery reuses the MCP gateway's ``call_tool`` (a 'send' tool), the same
convention retrieval uses for 'search'. Non-MCP channels (e.g. a raw webhook)
need a driver adapter - a deliberate follow-up. Delivery is best-effort: a
failing channel is logged, never failing the run.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.mcp_gateway import MCPToolError, call_tool
from app.models.channel import Channel
from app.models.inbox_item import InboxItem
from app.repositories.mcp_servers import SqlAlchemyMCPServerRepository

logger = logging.getLogger(__name__)

# Convention: an outbound channel's MCP server exposes a 'send' tool.
SEND_TOOL = "send"


async def _outbound_channels_for(session: AsyncSession, item_type: str) -> list[Channel]:
    result = await session.execute(
        select(Channel).where(Channel.enabled.is_(True), Channel.direction.in_(("out", "both")))
    )
    channels = result.scalars().all()
    # An empty routing list means the channel accepts every item type.
    return [c for c in channels if not c.routing or item_type in c.routing]


async def _send(channel: Channel, server, item: InboxItem) -> bool:
    if server is None:
        # Non-MCP channels (e.g. a raw webhook) need a driver adapter - a follow-up.
        logger.info("channel %s has no MCP server; skipping delivery", channel.id)
        return False
    try:
        await call_tool(
            server,
            SEND_TOOL,
            {"type": item.type, "run_id": item.run_id, "payload": item.payload},
        )
        return True
    except MCPToolError:
        logger.warning("delivery to channel %s failed", channel.id, exc_info=True)
        return False


async def route_and_deliver(session: AsyncSession, item: InboxItem) -> list[str]:
    """Route an inbox item to matching channels; record + return the targets.

    Sets ``item.channel_ids`` to the matched channels and best-effort delivers to
    each. The caller commits to persist ``channel_ids``.
    """
    channels = await _outbound_channels_for(session, item.type)
    item.channel_ids = [c.id for c in channels]
    mcp_repo = SqlAlchemyMCPServerRepository(session)
    delivered: list[str] = []
    for channel in channels:
        server = await mcp_repo.get(channel.mcp_server_id) if channel.mcp_server_id else None
        if await _send(channel, server, item):
            delivered.append(channel.id)
    return delivered
