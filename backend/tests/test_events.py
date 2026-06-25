"""Tests for event-mode triggers (M5.3).

event_targets is pure (source + subset-filter matching); the /events endpoint is
exercised end-to-end with a stubbed model, confirming a matching event fires a
run and a non-matching one does not.
"""

from app.integrations.litellm_gateway import CompletionResult
from app.models.trigger import Trigger
from app.triggers.events import event_targets


def _event_trigger(source, event_filter, *, mode="event", enabled=True) -> Trigger:
    return Trigger(
        agent_id="a", mode=mode, event_source=source, event_filter=event_filter, enabled=enabled
    )


def test_event_targets_filters_by_source_and_filter():
    match = _event_trigger("github", {"action": "opened"})
    wrong_source = _event_trigger("gitlab", {})
    filter_miss = _event_trigger("github", {"action": "closed"})
    disabled = _event_trigger("github", {}, enabled=False)
    wrong_mode = _event_trigger("github", {}, mode="scheduled")
    payload = {"action": "opened", "number": 5}

    targets = event_targets(
        [match, wrong_source, filter_miss, disabled, wrong_mode], "github", payload
    )

    assert targets == [match]


async def _agent_with_llm(client) -> str:
    conn = (
        await client.post(
            "/llm-connections", json={"name": "c", "provider_model": "openai/gpt-4o-mini"}
        )
    ).json()
    agent = (
        await client.post(
            "/agents", json={"name": "A", "goal": "react", "llm_connection_id": conn["id"]}
        )
    ).json()
    return agent["id"]


async def test_publish_event_fires_only_matching_trigger(client, monkeypatch):
    async def fake_complete(connection, messages, tools=None, **kw):
        return CompletionResult(content="handled", model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)
    agent_id = await _agent_with_llm(client)
    trigger = (
        await client.post(
            "/triggers",
            json={
                "agent_id": agent_id,
                "mode": "event",
                "event_source": "github",
                "event_filter": {"action": "opened"},
            },
        )
    ).json()

    matching = await client.post(
        "/events", json={"source": "github", "payload": {"action": "opened", "number": 1}}
    )
    assert matching.status_code == 200
    assert matching.json()["fired"] == 1

    runs = (await client.get("/runs")).json()
    assert len(runs) == 1
    assert runs[0]["trigger_id"] == trigger["id"]
    assert runs[0]["status"] == "completed"

    # Same source, filter does not match -> no fire.
    non_matching = await client.post(
        "/events", json={"source": "github", "payload": {"action": "closed"}}
    )
    assert non_matching.json()["fired"] == 0
    assert len((await client.get("/runs")).json()) == 1
