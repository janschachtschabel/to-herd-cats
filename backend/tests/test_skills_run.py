"""Skills wiring: an agent's enabled skills' instructions reach the run's prompt."""

from app.integrations.litellm_gateway import CompletionResult
from app.models.agent import Agent
from app.runtime.executor import system_prompt


def test_system_prompt_appends_skill_instructions():
    agent = Agent(name="A", role="analyst", instructions="Be concise.")
    prompt = system_prompt(agent, skills="## Skill: Bullets\nAnswer in bullet points.")
    assert "Be concise." in prompt
    assert "Answer in bullet points." in prompt


def _capture_llm(monkeypatch) -> dict:
    captured: dict = {}

    async def fake_complete(connection, messages, **kwargs):
        captured["messages"] = messages
        return CompletionResult(content="done", model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)
    return captured


async def _agent_with_skill(client, *, enabled: bool) -> str:
    conn = (
        await client.post(
            "/llm-connections", json={"name": "c", "provider_model": "openai/gpt-4o-mini"}
        )
    ).json()
    skill = (
        await client.post(
            "/skills",
            json={
                "name": "Bullets",
                "description": "answer in bullets",
                "instructions": "Always answer in bullet points.",
                "enabled": enabled,
            },
        )
    ).json()
    agent = (
        await client.post(
            "/agents",
            json={"name": "A", "llm_connection_id": conn["id"], "skill_ids": [skill["id"]]},
        )
    ).json()
    return agent["id"]


def _system_text(captured: dict) -> str:
    return " ".join(m["content"] for m in captured["messages"] if m["role"] == "system")


async def test_run_injects_enabled_skill_into_the_system_prompt(client, monkeypatch):
    captured = _capture_llm(monkeypatch)
    agent_id = await _agent_with_skill(client, enabled=True)

    await client.post(f"/agents/{agent_id}/runs", json={"goal": "hi"})

    assert "Always answer in bullet points." in _system_text(captured)


async def test_disabled_skill_is_not_injected(client, monkeypatch):
    captured = _capture_llm(monkeypatch)
    agent_id = await _agent_with_skill(client, enabled=False)

    await client.post(f"/agents/{agent_id}/runs", json={"goal": "hi"})

    assert "bullet points" not in _system_text(captured)
