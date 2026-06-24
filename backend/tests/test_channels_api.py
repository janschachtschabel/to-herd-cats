"""End-to-end CRUD over HTTP for channels, incl. SecretRef connection."""


async def test_create_webhook_channel(client):
    payload = {
        "name": "Ops webhook",
        "kind": "webhook",
        "connection_ref": "env:SLACK_WEBHOOK",
        "direction": "out",
        "routing": ["approval_request", "notification"],
    }
    resp = await client.post("/channels", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["kind"] == "webhook"
    assert body["connection_ref"] == "env:SLACK_WEBHOOK"
    assert body["direction"] == "out"
    assert body["routing"] == ["approval_request", "notification"]


async def test_reject_plaintext_connection(client):
    resp = await client.post(
        "/channels",
        json={"name": "X", "kind": "slack", "connection_ref": "xoxb-real-token"},
    )
    assert resp.status_code == 422


async def test_reject_invalid_kind(client):
    resp = await client.post("/channels", json={"name": "X", "kind": "telegraph"})
    assert resp.status_code == 422


async def test_crud_roundtrip(client):
    created = (await client.post("/channels", json={"name": "C", "kind": "email"})).json()
    cid = created["id"]
    assert (await client.get(f"/channels/{cid}")).status_code == 200
    upd = await client.patch(f"/channels/{cid}", json={"direction": "both"})
    assert upd.json()["direction"] == "both"
    assert {c["name"] for c in (await client.get("/channels")).json()} == {"C"}
    assert (await client.delete(f"/channels/{cid}")).status_code == 204
    assert (await client.get(f"/channels/{cid}")).status_code == 404
