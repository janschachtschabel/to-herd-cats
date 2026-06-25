"""MCP gateway: discover the tools a registered MCP server exposes.

A pure adapter. It connects to an MCPServer over its transport (stdio or
streamable HTTP), lists the server's tools, and returns normalized descriptors.
Routing agents' tool *calls* through a gateway (MCPJungle) is a later concern;
discovery needs a direct connection, which is what this module does.

Discovery is currently unauthenticated; resolving a server's ``credentials_ref``
into auth headers is a follow-up.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from app.models.mcp_server import MCPServer


class MCPDiscoveryError(RuntimeError):
    """Raised when an MCP server cannot be reached or queried."""


async def tools_from_session(session: ClientSession) -> list[dict[str, Any]]:
    """List and normalize the tools exposed by an initialized MCP session."""
    result = await session.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema or {},
        }
        for tool in result.tools
    ]


@asynccontextmanager
async def _connect(server: MCPServer) -> AsyncIterator[ClientSession]:
    """Open and initialize a client session for the server's transport."""
    if server.transport == "stdio":
        if not server.command:
            raise MCPDiscoveryError("stdio transport requires a command")
        params = StdioServerParameters(command=server.command, args=list(server.args or []))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    elif server.transport == "streamable_http":
        if not server.url:
            raise MCPDiscoveryError("streamable_http transport requires a url")
        async with streamablehttp_client(server.url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    else:
        raise MCPDiscoveryError(f"unsupported transport {server.transport!r}")


async def discover_tools(server: MCPServer) -> list[dict[str, Any]]:
    """Connect to ``server`` and return its tools as normalized descriptors."""
    try:
        async with _connect(server) as session:
            return await tools_from_session(session)
    except MCPDiscoveryError:
        raise
    except Exception as exc:  # connection / protocol failures
        raise MCPDiscoveryError(f"discovery failed for {server.name!r}: {exc}") from exc
