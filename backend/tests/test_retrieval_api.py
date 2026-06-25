"""End-to-end tests for data-source retrieval (M4.5).

The MCP search (retrieval.call_tool) and the model (graph.complete) are stubbed;
the test confirms retrieved context is injected into the agent's prompt, and
that a failing search is skipped without failing the run.
"""

from app.integrations.litellm_gateway import CompletionResult
from app.integrations.mcp_gateway import MCPToolError


async def _agent_with_data_source(client) -> str:
    conn = (
        await client.post(
            "/llm-connections",
            json={"name": "c", "provider_model": "openai/gpt-4o-mini"},
        )
    ).json()
    server = (
        await client.post("/mcp-servers", json={"name": "s", "transport": "stdio", "command": "x"})
    ).json()
    ds = (
        await client.post(
            "/data-sources",
            json={
                "name": "KB",
                "kind": "vector",
                "mcp_server_id": server["id"],
                "capabilities": ["search"],
            },
        )
    ).json()
    agent = (
        await client.post(
            "/agents",
            json={
                "name": "A",
                "llm_connection_id": conn["id"],
                "data_source_ids": [ds["id"]],
            },
        )
    ).json()
    return agent["id"]


async def test_retrieved_context_is_injected(client, monkeypatch):
    async def fake_call_tool(server, tool_name, arguments):
        assert tool_name == "search"
        assert arguments == {"query": "what colour is the sky?"}
        return "The sky is blue."

    monkeypatch.setattr("app.runtime.retrieval.call_tool", fake_call_tool)

    captured = {}

    async def fake_complete(connection, messages, tools=None, **kw):
        captured["messages"] = messages
        return CompletionResult(content="Blue.", model="mock", total_tokens=2)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)
    agent_id = await _agent_with_data_source(client)

    run = (
        await client.post(f"/agents/{agent_id}/runs", json={"goal": "what colour is the sky?"})
    ).json()
    assert run["status"] == "completed"
    joined = " ".join(
        m["content"] for m in captured["messages"] if isinstance(m.get("content"), str)
    )
    assert "The sky is blue." in joined  # retrieved context reached the prompt
    assert "[KB]" in joined  # labelled by the data source's name


async def test_search_failure_is_skipped(client, monkeypatch):
    async def boom(server, tool_name, arguments):
        raise MCPToolError("unreachable")

    monkeypatch.setattr("app.runtime.retrieval.call_tool", boom)

    captured = {}

    async def fake_complete(connection, messages, tools=None, **kw):
        captured["messages"] = messages
        return CompletionResult(content="ok", model="mock", total_tokens=1)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)
    agent_id = await _agent_with_data_source(client)

    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "x"})).json()
    assert run["status"] == "completed"  # the run still completes
    assert not any("Relevant context" in (m.get("content") or "") for m in captured["messages"])
