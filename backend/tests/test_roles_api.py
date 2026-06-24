"""End-to-end CRUD over HTTP for roles."""


async def test_create_role(client):
    payload = {
        "name": "Editor",
        "description": "Can manage agents and tools",
        "permissions": ["agent.create", "tool.manage"],
    }
    resp = await client.post("/roles", json=payload)
    assert resp.status_code == 201
    assert resp.json()["permissions"] == ["agent.create", "tool.manage"]


async def test_name_required(client):
    resp = await client.post("/roles", json={"permissions": ["x"]})
    assert resp.status_code == 422


async def test_crud_roundtrip(client):
    created = (await client.post("/roles", json={"name": "Viewer"})).json()
    rid = created["id"]
    assert (await client.get(f"/roles/{rid}")).status_code == 200
    upd = await client.patch(f"/roles/{rid}", json={"permissions": ["run.approve"]})
    assert upd.json()["permissions"] == ["run.approve"]
    assert {r["name"] for r in (await client.get("/roles")).json()} == {"Viewer"}
    assert (await client.delete(f"/roles/{rid}")).status_code == 204
    assert (await client.get(f"/roles/{rid}")).status_code == 404
