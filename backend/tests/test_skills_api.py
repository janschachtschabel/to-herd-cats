"""End-to-end CRUD over HTTP for the Skill resource."""


async def test_create_skill_with_command(client):
    payload = {
        "name": "Research report",
        "description": "Gather sources and produce a structured research report",
        "instructions": "1. Search. 2. Synthesise. 3. Cite.",
        "invocation": "both",
        "commands": [{"command": "/research", "input_schema": {"type": "object"}}],
        "requires_approval": True,
    }
    resp = await client.post("/skills", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["invocation"] == "both"
    assert body["commands"][0]["command"] == "/research"
    assert body["requires_approval"] is True
    assert body["source"] == "inline"
    assert body["enabled"] is True


async def test_description_is_required(client):
    resp = await client.post("/skills", json={"name": "No description"})
    assert resp.status_code == 422


async def test_invalid_invocation_rejected(client):
    resp = await client.post(
        "/skills",
        json={"name": "S", "description": "d", "invocation": "telepathy"},
    )
    assert resp.status_code == 422


async def test_crud_roundtrip(client):
    created = (
        await client.post("/skills", json={"name": "S", "description": "does a thing"})
    ).json()
    sid = created["id"]

    assert (await client.get(f"/skills/{sid}")).status_code == 200

    updated = await client.patch(
        f"/skills/{sid}", json={"enabled": False, "invocation": "command"}
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert updated.json()["invocation"] == "command"
    assert updated.json()["description"] == "does a thing"  # untouched

    assert {s["name"] for s in (await client.get("/skills")).json()} == {"S"}

    assert (await client.delete(f"/skills/{sid}")).status_code == 204
    assert (await client.get(f"/skills/{sid}")).status_code == 404
