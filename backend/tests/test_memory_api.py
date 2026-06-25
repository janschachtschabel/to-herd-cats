"""End-to-end tests for cross-run agent memory (M4.6).

The embedding call (memory.embed) and the model (graph.complete) are stubbed.
The tests confirm a completed run is remembered, and that the next run of the
same agent recalls it per the agent's memory mode (long / short / none).
"""

from app.integrations.litellm_gateway import CompletionResult
from app.runtime.memory import cosine


async def _make_connection(client) -> str:
    conn = (
        await client.post(
            "/llm-connections",
            json={"name": "c", "provider_model": "openai/gpt-4o-mini"},
        )
    ).json()
    return conn["id"]


async def _make_agent(client, conn_id: str, mode: str) -> str:
    agent = (
        await client.post(
            "/agents",
            json={"name": "A", "llm_connection_id": conn_id, "memory": {"mode": mode}},
        )
    ).json()
    return agent["id"]


def _join(messages) -> str:
    return " ".join(m["content"] for m in messages if isinstance(m.get("content"), str))


def test_cosine_similarity_handles_edge_cases():
    assert cosine([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine([], [1.0]) == 0.0  # length mismatch
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0  # zero norm


async def test_long_term_memory_recall_ranks_by_similarity(client, monkeypatch):
    # France-related text maps to one axis, everything else to another.
    async def fake_embed(connection, text):
        france = "france" in text.lower() or "paris" in text.lower()
        return [1.0, 0.0] if france else [0.0, 1.0]

    monkeypatch.setattr("app.runtime.memory.embed", fake_embed)

    prompts: list = []

    async def fake_complete(connection, messages, tools=None, **kw):
        prompts.append(messages)
        goal = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        answer = (
            "Paris is the capital of France."
            if "france" in goal.lower()
            else "Two plus two is four."
        )
        return CompletionResult(content=answer, model="mock", total_tokens=3)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)

    conn = await _make_connection(client)
    agent = await _make_agent(client, conn, "long")

    # An unrelated memory (the distractor) plus one about France.
    await client.post(f"/agents/{agent}/runs", json={"goal": "How much is two plus two?"})
    await client.post(f"/agents/{agent}/runs", json={"goal": "What is the capital of France?"})

    # A France query must rank the France memory above the unrelated distractor.
    await client.post(f"/agents/{agent}/runs", json={"goal": "tell me about France"})
    recalled = _join(prompts[-1])
    assert "Memory from past interactions" in recalled
    assert "Paris is the capital of France." in recalled
    assert recalled.index("Paris is the capital of France.") < recalled.index(
        "Two plus two is four."
    )


async def test_short_term_memory_recalls_recent(client, monkeypatch):
    prompts: list = []

    async def fake_complete(connection, messages, tools=None, **kw):
        prompts.append(messages)
        return CompletionResult(content="answer-one", model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)

    conn = await _make_connection(client)
    agent = await _make_agent(client, conn, "short")

    await client.post(f"/agents/{agent}/runs", json={"goal": "first goal"})
    await client.post(f"/agents/{agent}/runs", json={"goal": "second goal"})

    recalled = _join(prompts[-1])
    assert "Memory from past interactions" in recalled
    assert "first goal" in recalled  # the recent interaction is recalled verbatim
    assert "answer-one" in recalled


async def test_no_memory_when_mode_none(client, monkeypatch):
    prompts: list = []

    async def fake_complete(connection, messages, tools=None, **kw):
        prompts.append(messages)
        return CompletionResult(content="answer", model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)

    conn = await _make_connection(client)
    agent = await _make_agent(client, conn, "none")

    await client.post(f"/agents/{agent}/runs", json={"goal": "first"})
    await client.post(f"/agents/{agent}/runs", json={"goal": "second"})

    assert "Memory from past interactions" not in _join(prompts[-1])
