"""End-to-end tests for run comparison (M4.4b)."""

from app.integrations.litellm_gateway import CompletionResult


async def _echo_agent(client, monkeypatch) -> str:
    conn = (
        await client.post(
            "/llm-connections",
            json={"name": "c", "provider_model": "openai/gpt-4o-mini"},
        )
    ).json()
    agent = (
        await client.post("/agents", json={"name": "A", "llm_connection_id": conn["id"]})
    ).json()

    async def fake_complete(connection, messages, tools=None, **kw):
        goal = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return CompletionResult(content=goal, model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)
    return agent["id"]


async def test_compare_two_runs(client, monkeypatch):
    agent_id = await _echo_agent(client, monkeypatch)
    run_a = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "alpha"})).json()
    run_b = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "beta"})).json()

    resp = await client.post(
        "/runs/compare",
        json={"run_a_id": run_a["id"], "run_b_id": run_b["id"], "fields": ["content"]},
    )
    assert resp.status_code == 200
    comp = resp.json()["comparison"]
    assert comp["all_equal"] is False
    row = next(r for r in comp["fields"] if r["field"] == "content")
    assert row["a"] == "alpha" and row["b"] == "beta"
    assert row["equal"] is False


async def test_compare_renders_with_template(client, monkeypatch):
    agent_id = await _echo_agent(client, monkeypatch)
    run_a = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "same"})).json()
    run_b = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "same"})).json()
    tmpl = (
        await client.post(
            "/templates",
            json={
                "name": "C",
                "kind": "comparison",
                "render_template": "all_equal={{ all_equal }}",
            },
        )
    ).json()

    resp = await client.post(
        "/runs/compare",
        json={
            "run_a_id": run_a["id"],
            "run_b_id": run_b["id"],
            "template_id": tmpl["id"],
        },
    )
    body = resp.json()
    assert body["comparison"]["all_equal"] is True
    assert body["rendered"] == "all_equal=True"


async def test_compare_unknown_run_404(client, monkeypatch):
    agent_id = await _echo_agent(client, monkeypatch)
    run_a = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "x"})).json()
    resp = await client.post("/runs/compare", json={"run_a_id": run_a["id"], "run_b_id": "nope"})
    assert resp.status_code == 404
