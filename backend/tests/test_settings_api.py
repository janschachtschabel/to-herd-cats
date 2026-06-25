"""End-to-end tests for the scoped key/value Setting store (upsert via PUT)."""


async def test_upsert_creates_then_updates(client):
    r1 = await client.put("/settings/global/theme", json={"value": "dark"})
    assert r1.status_code == 200
    assert r1.json()["value"] == "dark"
    assert r1.json()["scope"] == "global"

    r2 = await client.put("/settings/global/theme", json={"value": "light"})
    assert r2.json()["value"] == "light"

    # Upsert must not create a duplicate.
    listing = (await client.get("/settings")).json()
    assert len([s for s in listing if s["key"] == "theme"]) == 1


async def test_scope_filter(client):
    await client.put("/settings/global/lang", json={"value": "de"})
    await client.put("/settings/user/lang", json={"value": "en"})

    got = await client.get("/settings/global/lang")
    assert got.status_code == 200
    assert got.json()["value"] == "de"

    only_user = (await client.get("/settings?scope=user")).json()
    assert {s["scope"] for s in only_user} == {"user"}


async def test_value_can_be_object(client):
    r = await client.put("/settings/global/limits", json={"value": {"max": 10, "tags": ["a", "b"]}})
    assert r.json()["value"] == {"max": 10, "tags": ["a", "b"]}


async def test_missing_returns_404(client):
    assert (await client.get("/settings/global/nope")).status_code == 404


async def test_invalid_scope_rejected(client):
    assert (await client.put("/settings/galaxy/x", json={"value": 1})).status_code == 422


async def test_delete(client):
    await client.put("/settings/global/temp", json={"value": 1})
    assert (await client.delete("/settings/global/temp")).status_code == 204
    assert (await client.get("/settings/global/temp")).status_code == 404
