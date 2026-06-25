"""Tests for autonomous-mode triggers (M5.2).

run_autonomous is exercised directly with a stubbed model and an injected sleep:
it fires once per iteration, sleeps between iterations (not after the last), and
stops when the iteration budget is spent. The fire endpoint's single-fire path
(non-autonomous modes) is covered too.
"""

from app.integrations.litellm_gateway import CompletionResult
from app.triggers.autonomous import run_autonomous


async def _agent_with_llm(client) -> str:
    conn = (
        await client.post(
            "/llm-connections", json={"name": "c", "provider_model": "openai/gpt-4o-mini"}
        )
    ).json()
    agent = (
        await client.post(
            "/agents",
            json={"name": "A", "goal": "keep working", "llm_connection_id": conn["id"]},
        )
    ).json()
    return agent["id"]


async def test_autonomous_loop_stops_on_iteration_budget(client, session_factory, monkeypatch):
    async def fake_complete(connection, messages, tools=None, **kw):
        return CompletionResult(content="step", model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)
    agent_id = await _agent_with_llm(client)

    slept: list[float] = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    run_ids = await run_autonomous(
        session_factory,
        agent_id,
        None,
        {"budget": {"iterations": 3}, "interval": 5},
        sleep=fake_sleep,
    )

    assert len(run_ids) == 3  # stopped exactly at the budget
    assert slept == [5, 5]  # slept between iterations, not after the last
    runs = (await client.get("/runs")).json()
    assert len(runs) == 3
    assert all(r["status"] == "completed" for r in runs)


async def test_fire_endpoint_runs_non_autonomous_trigger_once(client, monkeypatch):
    async def fake_complete(connection, messages, tools=None, **kw):
        return CompletionResult(content="done", model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)
    agent_id = await _agent_with_llm(client)
    trigger = (
        await client.post(
            "/triggers",
            json={"agent_id": agent_id, "mode": "scheduled", "cron": "* * * * *"},
        )
    ).json()

    resp = await client.post(f"/triggers/{trigger['id']}/fire")
    assert resp.status_code == 200
    assert resp.json()["run_id"]

    runs = (await client.get("/runs")).json()
    assert len(runs) == 1
    assert runs[0]["trigger_id"] == trigger["id"]
    assert runs[0]["status"] == "completed"
