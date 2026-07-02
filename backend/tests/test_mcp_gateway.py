"""Tests for the MCP discovery gateway.

The happy path runs a real in-memory FastMCP server and a real client session
(via the SDK's memory helper), so it exercises the actual MCP protocol and our
normalization — not a hand-rolled mock. The error paths cover transport
validation, which is pure logic.
"""

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session

from app.core.secret_ref import SecretResolutionError
from app.integrations.mcp_gateway import (
    MCPDiscoveryError,
    _auth_headers,
    call_tool_on_session,
    discover_tools,
    tools_from_session,
)
from app.models.mcp_server import MCPServer


def _server_with_tool() -> FastMCP:
    server = FastMCP("test")

    @server.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    return server


async def test_tools_from_real_session():
    server = _server_with_tool()
    async with create_connected_server_and_client_session(server._mcp_server) as session:
        tools = await tools_from_session(session)

    assert len(tools) == 1
    assert tools[0]["name"] == "add"
    assert tools[0]["description"] == "Add two numbers."
    assert tools[0]["input_schema"]  # non-empty JSON Schema


def test_auth_headers_none_without_credentials():
    assert _auth_headers(MCPServer(name="x", transport="streamable_http")) is None


def test_auth_headers_resolves_bearer_token(monkeypatch):
    monkeypatch.setenv("MY_MCP_TOKEN", "s3cr3t")
    server = MCPServer(name="x", transport="streamable_http", credentials_ref="env:MY_MCP_TOKEN")
    assert _auth_headers(server) == {"Authorization": "Bearer s3cr3t"}


def test_auth_headers_raises_when_secret_missing():
    server = MCPServer(name="x", transport="streamable_http", credentials_ref="env:UNSET_MCP_TOKEN")
    with pytest.raises(SecretResolutionError):
        _auth_headers(server)


async def test_discover_rejects_unsupported_transport():
    server = MCPServer(name="x", transport="carrier-pigeon")
    with pytest.raises(MCPDiscoveryError):
        await discover_tools(server)


async def test_discover_requires_command_for_stdio():
    server = MCPServer(name="x", transport="stdio")  # no command
    with pytest.raises(MCPDiscoveryError):
        await discover_tools(server)


async def test_discover_requires_url_for_streamable_http():
    server = MCPServer(name="x", transport="streamable_http")  # no url
    with pytest.raises(MCPDiscoveryError):
        await discover_tools(server)


async def test_call_tool_on_session_returns_text():
    server = _server_with_tool()
    async with create_connected_server_and_client_session(server._mcp_server) as session:
        out = await call_tool_on_session(session, "add", {"a": 2, "b": 3})
    assert "5" in out


async def test_call_tool_on_session_reports_tool_error():
    server = FastMCP("test")

    @server.tool()
    def boom() -> int:
        """Always fails."""
        raise ValueError("nope")

    async with create_connected_server_and_client_session(server._mcp_server) as session:
        out = await call_tool_on_session(session, "boom", {})
    assert out.startswith("Error")
