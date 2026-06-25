"""Tests for the observability metrics summary (M6.1)."""

from app.integrations.litellm_gateway import CompletionResult


async def test_metrics_summary_aggregates_runs(client, monkeypatch):
    async def fake_complete(connection, messages, tools=None, **kw):
        return CompletionResult(content="ok", model="mock", total_tokens=5, cost=0.25)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)

    conn = (
        await client.post(
            "/llm-connections", json={"name": "c", "provider_model": "openai/gpt-4o-mini"}
        )
    ).json()
    agent = (
        await client.post("/agents", json={"name": "A", "llm_connection_id": conn["id"]})
    ).json()
    for _ in range(2):
        await client.post(f"/agents/{agent['id']}/runs", json={"goal": "go"})

    summary = (await client.get("/metrics/summary")).json()
    assert summary["total_runs"] == 2
    assert summary["by_status"] == {"completed": 2}
    assert summary["total_tokens"] == 10
    assert summary["total_cost"] == 0.5


async def test_metrics_summary_empty(client):
    summary = (await client.get("/metrics/summary")).json()
    assert summary == {
        "total_runs": 0,
        "by_status": {},
        "total_tokens": 0,
        "total_cost": 0.0,
    }
