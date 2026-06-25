"""End-to-end tests for the postbox (M4.2): interrupt -> InboxItem -> resume.

The LLM call is stubbed via the verified gateway, but the interrupt/resume cycle
runs through REAL LangGraph (MemorySaver checkpointer), so the human-in-the-loop
state machine is genuinely exercised.
"""

from app.integrations.litellm_gateway import CompletionResult


async def _approval_agent(client) -> str:
    conn = (
        await client.post(
            "/llm-connections", json={"name": "c", "provider_model": "openai/gpt-4o-mini"}
        )
    ).json()
    agent = (
        await client.post(
            "/agents",
            json={
                "name": "A",
                "llm_connection_id": conn["id"],
                "guardrails": {"requires_approval_for": ["finalize"]},
            },
        )
    ).json()
    return agent["id"]


def _stub_llm(monkeypatch, content: str) -> None:
    async def fake_complete(connection, messages, **kw):
        return CompletionResult(content=content, model="mock", total_tokens=10)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)


async def test_inbox_empty_initially(client):
    assert (await client.get("/inbox")).json() == []


async def test_run_pauses_for_approval_then_resumes(client, monkeypatch):
    _stub_llm(monkeypatch, "Draft answer.")
    agent_id = await _approval_agent(client)

    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "do it"})).json()
    assert run["status"] == "waiting_human"
    assert run["thread_id"] == run["id"]

    inbox = [i for i in (await client.get("/inbox")).json() if i["run_id"] == run["id"]]
    assert len(inbox) == 1
    item = inbox[0]
    assert item["type"] == "approval_request"
    assert item["status"] == "pending"
    assert item["payload"]["description_md"] == "Draft answer."

    resp = await client.post(f"/inbox/{item['id']}/respond", json={"action": "accept"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["result"]["content"] == "Draft answer."

    answered = (await client.get(f"/inbox/{item['id']}")).json()
    assert answered["status"] == "answered"
    assert answered["response"]["action"] == "accept"


async def test_respond_reject_marks_rejected(client, monkeypatch):
    _stub_llm(monkeypatch, "Draft.")
    agent_id = await _approval_agent(client)
    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "x"})).json()
    item = next(i for i in (await client.get("/inbox")).json() if i["run_id"] == run["id"])

    resp = await client.post(f"/inbox/{item['id']}/respond", json={"action": "reject"})
    assert resp.json()["status"] == "completed"
    assert resp.json()["result"]["rejected"] is True


async def test_double_respond_conflict(client, monkeypatch):
    _stub_llm(monkeypatch, "D")
    agent_id = await _approval_agent(client)
    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "x"})).json()
    item = next(i for i in (await client.get("/inbox")).json() if i["run_id"] == run["id"])

    assert (
        await client.post(f"/inbox/{item['id']}/respond", json={"action": "accept"})
    ).status_code == 200
    second = await client.post(f"/inbox/{item['id']}/respond", json={"action": "accept"})
    assert second.status_code == 409


async def test_respond_unknown_item_404(client):
    resp = await client.post("/inbox/nope/respond", json={"action": "accept"})
    assert resp.status_code == 404


async def test_failed_resume_keeps_item_pending_for_retry(client, monkeypatch):
    _stub_llm(monkeypatch, "Draft.")
    agent_id = await _approval_agent(client)
    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "x"})).json()
    item = next(i for i in (await client.get("/inbox")).json() if i["run_id"] == run["id"])

    async def boom(*args, **kwargs):
        raise RuntimeError("transient resume failure")

    monkeypatch.setattr("app.services.runs.resume_run", boom)
    failed = await client.post(f"/inbox/{item['id']}/respond", json={"action": "accept"})
    assert failed.json()["status"] == "failed"

    # The item must stay pending (not "answered") so the human can try again.
    still = (await client.get(f"/inbox/{item['id']}")).json()
    assert still["status"] == "pending"

    # Retrying with a working resume succeeds (no 409 conflict).
    monkeypatch.undo()
    _stub_llm(monkeypatch, "Draft.")
    retry = await client.post(f"/inbox/{item['id']}/respond", json={"action": "accept"})
    assert retry.status_code == 200
    assert retry.json()["status"] == "completed"
