"""End-to-end CRUD over HTTP for data sources, incl. SecretRef DSN enforcement."""


async def test_create_vector_source(client):
    payload = {
        "name": "Qdrant",
        "kind": "vector",
        "connection_ref": {"driver": "qdrant", "dsn_ref": "env:QDRANT_URL"},
        "capabilities": ["read", "search"],
        "embedding_model": "intfloat/multilingual-e5-large",
        "dimension": 1024,
        "collection": "wlo",
    }
    resp = await client.post("/data-sources", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["kind"] == "vector"
    assert body["connection_ref"]["dsn_ref"] == "env:QDRANT_URL"
    assert body["dimension"] == 1024
    assert body["capabilities"] == ["read", "search"]


async def test_reject_plaintext_dsn(client):
    resp = await client.post(
        "/data-sources",
        json={
            "name": "X",
            "kind": "relational",
            "connection_ref": {"driver": "postgres", "dsn_ref": "postgres://u:p@h/db"},
        },
    )
    assert resp.status_code == 422


async def test_reject_invalid_kind(client):
    resp = await client.post("/data-sources", json={"name": "X", "kind": "blockchain"})
    assert resp.status_code == 422


async def test_crud_roundtrip(client):
    created = (
        await client.post("/data-sources", json={"name": "D", "kind": "wiki"})
    ).json()
    did = created["id"]
    assert (await client.get(f"/data-sources/{did}")).status_code == 200
    upd = await client.patch(f"/data-sources/{did}", json={"enabled": False})
    assert upd.json()["enabled"] is False
    assert {d["name"] for d in (await client.get("/data-sources")).json()} == {"D"}
    assert (await client.delete(f"/data-sources/{did}")).status_code == 204
    assert (await client.get(f"/data-sources/{did}")).status_code == 404
