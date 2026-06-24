"""End-to-end CRUD over HTTP for MCP servers, incl. SecretRef enforcement."""


async def test_create_and_status_default(client):
    payload = {
        "name": "Filesystem",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "credentials_ref": "env:FS_TOKEN",
        "config_schema": {"type": "object", "properties": {"token": {"type": "string"}}},
    }
    resp = await client.post("/mcp-servers", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["transport"] == "stdio"
    assert body["credentials_ref"] == "env:FS_TOKEN"
    assert body["status"] == "unknown"  # server-managed, not connected yet
    assert body["discovered_tools"] == []


async def test_reject_plaintext_credentials(client):
    resp = await client.post(
        "/mcp-servers",
        json={"name": "X", "transport": "stdio", "credentials_ref": "supersecret"},
    )
    assert resp.status_code == 422


async def test_reject_invalid_transport(client):
    resp = await client.post(
        "/mcp-servers", json={"name": "X", "transport": "carrier-pigeon"}
    )
    assert resp.status_code == 422


async def test_crud_roundtrip(client):
    created = (
        await client.post(
            "/mcp-servers",
            json={
                "name": "S",
                "transport": "streamable_http",
                "url": "https://mcp.example.org",
            },
        )
    ).json()
    sid = created["id"]

    assert (await client.get(f"/mcp-servers/{sid}")).status_code == 200
    upd = await client.patch(
        f"/mcp-servers/{sid}", json={"url": "https://mcp2.example.org"}
    )
    assert upd.json()["url"] == "https://mcp2.example.org"
    assert {s["name"] for s in (await client.get("/mcp-servers")).json()} == {"S"}
    assert (await client.delete(f"/mcp-servers/{sid}")).status_code == 204
    assert (await client.get(f"/mcp-servers/{sid}")).status_code == 404
