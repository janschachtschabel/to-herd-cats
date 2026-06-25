"""Tests for the cron scheduler (M5.1).

``due_triggers`` is pure (the clock is injected); ``run_due`` is exercised
end-to-end against the app DB with the model stubbed, confirming a scheduled
trigger fires exactly one run and does not double-fire on the next tick.
"""

from datetime import UTC, datetime, timedelta

from app.integrations.litellm_gateway import CompletionResult
from app.models.trigger import Trigger
from app.triggers.scheduler import due_triggers, run_due


def _trigger(cron, last_fired, *, mode="scheduled", enabled=True) -> Trigger:
    return Trigger(agent_id="a", mode=mode, cron=cron, last_fired_at=last_fired, enabled=enabled)


def test_due_triggers_selects_only_due_scheduled():
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    now = datetime(2026, 1, 1, 12, 6, tzinfo=UTC)
    due = _trigger("*/5 * * * *", base)  # next fire 12:05 <= 12:06 -> due
    not_yet = _trigger("*/5 * * * *", now)  # next fire 12:10 > now
    disabled = _trigger("* * * * *", base, enabled=False)
    wrong_mode = _trigger("* * * * *", base, mode="event")
    bad_cron = _trigger("nonsense", base)  # invalid cron is skipped, not raised

    assert due_triggers([due, not_yet, disabled, wrong_mode, bad_cron], now) == [due]


async def test_run_due_fires_scheduled_trigger(client, session_factory, monkeypatch):
    async def fake_complete(connection, messages, tools=None, **kw):
        return CompletionResult(content="done", model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)

    conn = (
        await client.post(
            "/llm-connections", json={"name": "c", "provider_model": "openai/gpt-4o-mini"}
        )
    ).json()
    agent = (
        await client.post(
            "/agents",
            json={"name": "A", "goal": "do the thing", "llm_connection_id": conn["id"]},
        )
    ).json()
    trigger = (
        await client.post(
            "/triggers",
            json={"agent_id": agent["id"], "mode": "scheduled", "cron": "* * * * *"},
        )
    ).json()

    # A time well after creation makes a per-minute cron due.
    now = datetime.now(UTC).replace(microsecond=0) + timedelta(minutes=5)
    assert await run_due(session_factory, now) == 1

    runs = (await client.get("/runs")).json()
    assert len(runs) == 1
    assert runs[0]["agent_id"] == agent["id"]
    assert runs[0]["trigger_id"] == trigger["id"]
    assert runs[0]["status"] == "completed"

    # last_fired_at is stamped, so an immediate re-tick does not double-fire.
    assert await run_due(session_factory, now) == 0
