"""End-to-end test for the agent<->tools loop (M4.3a-ii).

The LLM is stubbed (graph.complete) to request a tool then give a final answer,
and the MCP tool call is stubbed (tools.call_tool) - both are verified
collaborators (test_litellm_gateway, test_mcp_gateway). This exercises the loop,
tool resolution, and result feedback through the real LangGraph runtime.
"""

from app.integrations.litellm_gateway import CompletionResult


async def _agent_with_tool(client) -> str:
    conn = (
        await client.post(
            "/llm-connections",
            json={"name": "c", "provider_model": "openai/gpt-4o-mini"},
        )
    ).json()
    server = (
        await client.post("/mcp-servers", json={"name": "s", "transport": "stdio", "command": "x"})
    ).json()
    tool = (
        await client.post(
            "/tools",
            json={
                "name": "add",
                "type": "mcp",
                "mcp_server_id": server["id"],
                "tool_name": "add",
                "input_schema": {"type": "object"},
            },
        )
    ).json()
    agent = (
        await client.post(
            "/agents",
            json={
                "name": "A",
                "llm_connection_id": conn["id"],
                "tool_ids": [tool["id"]],
            },
        )
    ).json()
    return agent["id"]


async def test_agent_uses_a_tool(client, monkeypatch):
    calls = {"n": 0}

    async def fake_complete(connection, messages, tools=None, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            assert tools is not None  # the agent's tool schema was offered
            return CompletionResult(
                content="",
                model="mock",
                tool_calls=[{"id": "c1", "name": "add", "arguments": {"a": 2, "b": 3}}],
                assistant_message={
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "c1",
                            "type": "function",
                            "function": {"name": "add", "arguments": '{"a": 2, "b": 3}'},
                        }
                    ],
                },
            )
        # Second turn: the model now has the tool result fed back.
        assert any(m["role"] == "tool" and m["content"] == "5" for m in messages)
        return CompletionResult(content="The sum is 5.", model="mock", total_tokens=7)

    async def fake_call_tool(server, tool_name, arguments):
        assert tool_name == "add" and arguments == {"a": 2, "b": 3}
        return "5"

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)
    monkeypatch.setattr("app.runtime.tools.call_tool", fake_call_tool)

    agent_id = await _agent_with_tool(client)
    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "add 2 and 3"})).json()

    assert run["status"] == "completed"
    assert run["result"]["content"] == "The sum is 5."
    assert calls["n"] == 2  # looped: tool request -> execute -> final answer
