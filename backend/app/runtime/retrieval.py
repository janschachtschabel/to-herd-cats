"""Retrieval: ground a run in the agent's data sources before it reasons.

For each MCP-backed data source the runtime calls a ``search`` tool on the
source's MCP server with the run goal; the combined results are injected as
context into the agent's opening messages. A source that cannot be queried is
skipped, not fatal. Driver-backed (non-MCP) data sources are a follow-up.
"""

import logging
from dataclasses import dataclass

from app.integrations.mcp_gateway import MCPToolError, call_tool
from app.models.data_source import DataSource
from app.models.mcp_server import MCPServer

logger = logging.getLogger(__name__)

# Convention: an MCP data source exposes its retrieval as a ``search`` tool.
SEARCH_TOOL = "search"


@dataclass
class ResolvedDataSource:
    data_source: DataSource
    server: MCPServer | None


async def retrieve_context(sources: list[ResolvedDataSource], query: str) -> str:
    """Query each MCP-backed data source and return the combined context text."""
    chunks: list[str] = []
    for source in sources:
        if source.server is None:
            continue  # driver-backed retrieval is a follow-up
        try:
            result = await call_tool(source.server, SEARCH_TOOL, {"query": query})
        except MCPToolError:
            # A source that can't be queried is skipped, not fatal.
            logger.warning("retrieval skipped data source %s: search failed", source.data_source.id)
            continue
        if result and not result.startswith("Error"):
            chunks.append(f"[{source.data_source.name}]\n{result}")
    return "\n\n".join(chunks)
