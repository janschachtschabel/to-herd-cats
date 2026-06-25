"""End-to-end tests for on-demand runs (M4.1).

The LiteLLM call is stubbed via the already-verified gateway (`complete`), so
these test the run orchestration (create -> execute -> persist status/result)
without hitting a provider. The gateway itself is tested in test_litellm_gateway.
"""

from app.integrations.litellm_gateway import CompletionResult


async def _agent_with_llm(client) -> str:
    conn = (
        await client.post(
            "/llm-connections", json={"name": "c", "provider_model": "openai/gpt-4o-mini"}
        )
    ).json()
    agent = (
        await client.post(
            "/agents",
            json={"name": "A", "role": "analyst", "llm_connection_id": conn["id"]},
        )
    ).json()
    return agent["id"]


async def test_on_demand_run_completes(client, monkeypatch):
    async def fake_complete(connection, messages, **kw):
        return CompletionResult(content="Done.", model="mock", total_tokens=12, cost=0.001)

    monkeypatch.setattr("app.runtime.executor.complete", fake_complete)
    agent_id = await _agent_with_llm(client)

    resp = await client.post(f"/agents/{agent_id}/runs", json={"goal": "Summarise X"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "completed"
    assert body["result"]["content"] == "Done."
    assert body["metrics"]["tokens"] == 12
    assert body["started_at"] and body["finished_at"]


async def test_run_records_llm_failure(client, monkeypatch):
    async def boom(connection, messages, **kw):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr("app.runtime.executor.complete", boom)
    agent_id = await _agent_with_llm(client)

    resp = await client.post(f"/agents/{agent_id}/runs", json={"goal": "x"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "failed"
    assert "provider exploded" in body["result"]["error"]


async def test_run_requires_llm_connection(client):
    agent = (await client.post("/agents", json={"name": "NoLLM"})).json()
    resp = await client.post(f"/agents/{agent['id']}/runs", json={"goal": "x"})
    assert resp.status_code == 400


async def test_run_unknown_agent_404(client):
    resp = await client.post("/agents/nope/runs", json={"goal": "x"})
    assert resp.status_code == 404


async def test_run_rejects_empty_goal(client):
    agent_id = await _agent_with_llm(client)
    resp = await client.post(f"/agents/{agent_id}/runs", json={"goal": ""})
    assert resp.status_code == 422


async def test_get_and_list_runs(client, monkeypatch):
    async def fake_complete(connection, messages, **kw):
        return CompletionResult(content="ok", model="mock", total_tokens=3)

    monkeypatch.setattr("app.runtime.executor.complete", fake_complete)
    agent_id = await _agent_with_llm(client)
    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "x"})).json()

    assert (await client.get(f"/runs/{run['id']}")).status_code == 200
    assert any(r["id"] == run["id"] for r in (await client.get("/runs")).json())
