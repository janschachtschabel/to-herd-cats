"""End-to-end CRUD over HTTP for tools, incl. the FK link to an MCP server."""


async def test_create_builtin_tool_without_server(client):
    resp = await client.post("/tools", json={"name": "echo", "type": "builtin"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "builtin"
    assert body["mcp_server_id"] is None
    assert body["enabled"] is True


async def test_create_mcp_tool_links_to_server(client):
    server = (
        await client.post("/mcp-servers", json={"name": "S", "transport": "stdio"})
    ).json()
    resp = await client.post(
        "/tools",
        json={
            "name": "search",
            "type": "mcp",
            "mcp_server_id": server["id"],
            "tool_name": "web_search",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["mcp_server_id"] == server["id"]


async def test_invalid_type_rejected(client):
    resp = await client.post("/tools", json={"name": "T", "type": "magic"})
    assert resp.status_code == 422


async def test_crud_roundtrip(client):
    created = (await client.post("/tools", json={"name": "T", "type": "builtin"})).json()
    tid = created["id"]

    assert (await client.get(f"/tools/{tid}")).status_code == 200
    upd = await client.patch(f"/tools/{tid}", json={"requires_approval": True})
    assert upd.json()["requires_approval"] is True
    assert {t["name"] for t in (await client.get("/tools")).json()} == {"T"}
    assert (await client.delete(f"/tools/{tid}")).status_code == 204
    assert (await client.get(f"/tools/{tid}")).status_code == 404
