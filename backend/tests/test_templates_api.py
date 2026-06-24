"""End-to-end CRUD over HTTP for output templates."""


async def test_create_research_template(client):
    payload = {
        "name": "Research report",
        "kind": "research",
        "output_schema": {"type": "object"},
        "render_template": "# {{ title }}",
        "format": "markdown",
    }
    resp = await client.post("/templates", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["kind"] == "research"
    assert body["format"] == "markdown"
    assert body["render_template"] == "# {{ title }}"


async def test_reject_invalid_format(client):
    resp = await client.post(
        "/templates", json={"name": "X", "kind": "report", "format": "papyrus"}
    )
    assert resp.status_code == 422


async def test_crud_roundtrip(client):
    created = (
        await client.post("/templates", json={"name": "T", "kind": "comparison"})
    ).json()
    tid = created["id"]
    assert (await client.get(f"/templates/{tid}")).status_code == 200
    upd = await client.patch(f"/templates/{tid}", json={"format": "html"})
    assert upd.json()["format"] == "html"
    assert {t["name"] for t in (await client.get("/templates")).json()} == {"T"}
    assert (await client.delete(f"/templates/{tid}")).status_code == 204
    assert (await client.get(f"/templates/{tid}")).status_code == 404
