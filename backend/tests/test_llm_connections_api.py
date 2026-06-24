"""End-to-end CRUD over HTTP for LLM connections, incl. SecretRef enforcement."""


async def test_create_stores_secret_ref_not_plaintext(client):
    payload = {
        "name": "OpenAI",
        "provider_model": "openai/gpt-5.4",
        "api_key_ref": "env:OPENAI_API_KEY",
        "params": {"temperature": 0.2},
    }
    resp = await client.post("/llm-connections", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    # The stored value is the *reference*, never a plaintext key.
    assert body["api_key_ref"] == "env:OPENAI_API_KEY"
    assert body["provider_model"] == "openai/gpt-5.4"
    assert body["params"]["temperature"] == 0.2
    assert body["enabled"] is True


async def test_reject_plaintext_key(client):
    resp = await client.post(
        "/llm-connections",
        json={"name": "X", "provider_model": "openai/gpt", "api_key_ref": "sk-secret"},
    )
    assert resp.status_code == 422


async def test_crud_roundtrip(client):
    created = (
        await client.post(
            "/llm-connections",
            json={"name": "Local", "provider_model": "ollama/llama3"},
        )
    ).json()
    cid = created["id"]

    assert (await client.get(f"/llm-connections/{cid}")).status_code == 200

    updated = await client.patch(f"/llm-connections/{cid}", json={"enabled": False})
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert updated.json()["name"] == "Local"  # untouched

    assert {c["name"] for c in (await client.get("/llm-connections")).json()} == {"Local"}

    assert (await client.delete(f"/llm-connections/{cid}")).status_code == 204
    assert (await client.get(f"/llm-connections/{cid}")).status_code == 404


async def test_create_requires_provider_model(client):
    resp = await client.post("/llm-connections", json={"name": "No model"})
    assert resp.status_code == 422
