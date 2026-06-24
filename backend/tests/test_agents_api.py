"""End-to-end CRUD over HTTP for the Agent resource."""


async def test_create_and_get_agent(client):
    payload = {"name": "Researcher", "role": "analyst", "goal": "summarise sources"}
    created = await client.post("/agents", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Researcher"
    assert body["status"] == "draft"
    assert body["tool_ids"] == []
    assert body["skill_ids"] == []
    assert body["memory"] == {"mode": "none", "vector_store_ref": None}

    fetched = await client.get(f"/agents/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


async def test_list_agents(client):
    await client.post("/agents", json={"name": "A"})
    await client.post("/agents", json={"name": "B"})
    resp = await client.get("/agents")
    assert resp.status_code == 200
    assert {a["name"] for a in resp.json()} == {"A", "B"}


async def test_update_is_partial(client):
    created = (await client.post("/agents", json={"name": "Draft"})).json()
    resp = await client.patch(
        f"/agents/{created['id']}", json={"status": "active", "goal": "new goal"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "active"
    assert body["goal"] == "new goal"
    assert body["name"] == "Draft"  # untouched field stays


async def test_delete_then_missing(client):
    created = (await client.post("/agents", json={"name": "Temp"})).json()
    assert (await client.delete(f"/agents/{created['id']}")).status_code == 204
    assert (await client.get(f"/agents/{created['id']}")).status_code == 404


async def test_get_unknown_returns_404(client):
    assert (await client.get("/agents/does-not-exist")).status_code == 404


async def test_create_rejects_empty_name(client):
    resp = await client.post("/agents", json={"name": ""})
    assert resp.status_code == 422
