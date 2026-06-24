"""End-to-end CRUD over HTTP for triggers, incl. the FK + cascade to an agent."""


async def _make_agent(client) -> str:
    return (await client.post("/agents", json={"name": "Worker"})).json()["id"]


async def test_create_scheduled_trigger(client):
    agent_id = await _make_agent(client)
    payload = {
        "agent_id": agent_id,
        "mode": "scheduled",
        "cron": "0 8 * * *",
        "timezone": "Europe/Berlin",
    }
    resp = await client.post("/triggers", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["mode"] == "scheduled"
    assert body["cron"] == "0 8 * * *"
    assert body["agent_id"] == agent_id


async def test_create_autonomous_trigger_with_loop(client):
    agent_id = await _make_agent(client)
    payload = {
        "agent_id": agent_id,
        "mode": "autonomous",
        "loop_config": {"interval": 300, "stop_condition": "done", "budget": {"cost": 1.0}},
    }
    resp = await client.post("/triggers", json=payload)
    assert resp.status_code == 201
    assert resp.json()["loop_config"]["interval"] == 300


async def test_reject_invalid_mode(client):
    agent_id = await _make_agent(client)
    resp = await client.post("/triggers", json={"agent_id": agent_id, "mode": "telepathy"})
    assert resp.status_code == 422


async def test_cascade_delete_with_agent(client):
    agent_id = await _make_agent(client)
    trig = (
        await client.post("/triggers", json={"agent_id": agent_id, "mode": "on_demand"})
    ).json()
    # Deleting the agent cascades to its triggers (DB-level ON DELETE CASCADE).
    assert (await client.delete(f"/agents/{agent_id}")).status_code == 204
    assert (await client.get(f"/triggers/{trig['id']}")).status_code == 404


async def test_crud_roundtrip(client):
    agent_id = await _make_agent(client)
    created = (
        await client.post("/triggers", json={"agent_id": agent_id, "mode": "on_demand"})
    ).json()
    tid = created["id"]
    assert (await client.get(f"/triggers/{tid}")).status_code == 200
    upd = await client.patch(f"/triggers/{tid}", json={"enabled": False})
    assert upd.json()["enabled"] is False
    assert (await client.delete(f"/triggers/{tid}")).status_code == 204
    assert (await client.get(f"/triggers/{tid}")).status_code == 404
