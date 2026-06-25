"""Tests for POST /mcp-servers/{id}/discover.

Real discovery is covered in test_mcp_gateway against an in-memory MCP server;
here we stub that verified collaborator to test the endpoint's caching and
status logic.
"""

from app.integrations.mcp_gateway import MCPDiscoveryError


async def _make_server(client) -> str:
    resp = await client.post(
        "/mcp-servers", json={"name": "S", "transport": "stdio", "command": "x"}
    )
    return resp.json()["id"]


async def test_discover_caches_tools_and_sets_connected(client, monkeypatch):
    async def fake_discover(server):
        return [{"name": "search", "description": "Web search", "input_schema": {"type": "object"}}]

    monkeypatch.setattr("app.services.mcp_servers.discover_tools", fake_discover)
    server_id = await _make_server(client)

    resp = await client.post(f"/mcp-servers/{server_id}/discover")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "connected"
    assert [t["name"] for t in body["discovered_tools"]] == ["search"]


async def test_discover_records_error_status_and_502(client, monkeypatch):
    async def fake_discover(server):
        raise MCPDiscoveryError("unreachable")

    monkeypatch.setattr("app.services.mcp_servers.discover_tools", fake_discover)
    server_id = await _make_server(client)

    resp = await client.post(f"/mcp-servers/{server_id}/discover")
    assert resp.status_code == 502
    # The failed status is persisted so the UI can show it.
    got = await client.get(f"/mcp-servers/{server_id}")
    assert got.json()["status"] == "error"


async def test_discover_unknown_server_404(client):
    assert (await client.post("/mcp-servers/nope/discover")).status_code == 404
