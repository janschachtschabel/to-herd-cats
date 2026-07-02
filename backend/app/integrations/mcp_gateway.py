"""MCP gateway: discover the tools a registered MCP server exposes.

A pure adapter. It connects to an MCPServer over its transport (stdio or
streamable HTTP), lists the server's tools, and returns normalized descriptors.
Routing agents' tool *calls* through a gateway (MCPJungle) is a later concern;
discovery needs a direct connection, which is what this module does.

A server's ``credentials_ref`` (a SecretRef) is resolved to a bearer auth header
for streamable-HTTP transports; the plaintext token is only ever placed in the
outgoing header, never stored or logged. (stdio auth is via the subprocess
environment, out of scope here.)
"""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from app.core.secret_ref import resolve_secret
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


def _auth_headers(server: MCPServer) -> dict[str, str] | None:
    """Resolve the server's ``credentials_ref`` into a bearer auth header.

    Returns None when the server has no credentials. Raises SecretResolutionError
    if the reference cannot be resolved (e.g. the env var is unset).
    """
    if not server.credentials_ref:
        return None
    return {"Authorization": f"Bearer {resolve_secret(server.credentials_ref)}"}


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
        async with streamablehttp_client(server.url, headers=_auth_headers(server)) as (
            read,
            write,
            _,
        ):
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


class MCPToolError(RuntimeError):
    """Raised when an MCP tool call fails (connection or protocol failure)."""


def _result_text(result: object) -> str:
    parts = [b.text for b in result.content if getattr(b, "text", None)]
    if parts:
        text = "\n".join(parts)
    else:
        structured = getattr(result, "structuredContent", None)
        text = json.dumps(structured) if structured is not None else ""
    if getattr(result, "isError", False):
        return f"Error: {text}" if text else "Error: tool returned an error"
    return text


async def call_tool_on_session(session: ClientSession, tool_name: str, arguments: dict) -> str:
    """Call a tool on an initialized session and render the result as text."""
    result = await session.call_tool(tool_name, arguments)
    return _result_text(result)


async def call_tool(server: MCPServer, tool_name: str, arguments: dict) -> str:
    """Connect to ``server`` and call ``tool_name``; render the result as text.

    A tool that returns an error result yields an ``"Error: ..."`` string (so it
    can be fed back to the model); a connection/protocol failure raises
    MCPToolError.
    """
    try:
        async with _connect(server) as session:
            return await call_tool_on_session(session, tool_name, arguments)
    except Exception as exc:
        raise MCPToolError(f"tool call failed for {tool_name!r}: {exc}") from exc
