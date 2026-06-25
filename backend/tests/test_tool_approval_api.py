"""End-to-end tests for per-tool approval (M4.3b).

A tool with requires_approval pauses the run for approval BEFORE it executes
(checked via an execution counter); approving runs it exactly once (guarding the
LangGraph node-re-run gotcha), rejecting skips it and feeds back a rejection.
Real LangGraph interrupt/resume; the model and the MCP call are stubbed
(verified collaborators).
"""

from app.integrations.litellm_gateway import CompletionResult


async def _agent_with_approval_tool(client) -> str:
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
                "name": "danger",
                "type": "mcp",
                "mcp_server_id": server["id"],
                "tool_name": "danger",
                "requires_approval": True,
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


def _stub_two_turn_llm(monkeypatch) -> None:
    state = {"n": 0}

    async def fake_complete(connection, messages, tools=None, **kw):
        state["n"] += 1
        if state["n"] == 1:
            return CompletionResult(
                content="",
                model="mock",
                tool_calls=[{"id": "c1", "name": "danger", "arguments": {}}],
                assistant_message={
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "c1",
                            "type": "function",
                            "function": {"name": "danger", "arguments": "{}"},
                        }
                    ],
                },
            )
        return CompletionResult(content="Done.", model="mock", total_tokens=4)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)


async def test_tool_approval_pauses_before_executing_then_runs(client, monkeypatch):
    _stub_two_turn_llm(monkeypatch)
    executed = {"n": 0}

    async def fake_call_tool(server, tool_name, arguments):
        executed["n"] += 1
        return "tool-ran"

    monkeypatch.setattr("app.runtime.tools.call_tool", fake_call_tool)
    agent_id = await _agent_with_approval_tool(client)

    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "go"})).json()
    assert run["status"] == "waiting_human"
    assert executed["n"] == 0  # paused BEFORE executing the tool

    item = next(i for i in (await client.get("/inbox")).json() if i["run_id"] == run["id"])
    assert item["payload"]["tool_calls"][0]["name"] == "danger"

    resp = await client.post(f"/inbox/{item['id']}/respond", json={"action": "accept"})
    assert resp.json()["status"] == "completed"
    assert resp.json()["result"]["content"] == "Done."
    assert executed["n"] == 1  # executed exactly once after approval (no double-run)


async def test_tool_approval_reject_skips_execution(client, monkeypatch):
    _stub_two_turn_llm(monkeypatch)
    executed = {"n": 0}

    async def fake_call_tool(server, tool_name, arguments):
        executed["n"] += 1
        return "tool-ran"

    monkeypatch.setattr("app.runtime.tools.call_tool", fake_call_tool)
    agent_id = await _agent_with_approval_tool(client)

    run = (await client.post(f"/agents/{agent_id}/runs", json={"goal": "go"})).json()
    item = next(i for i in (await client.get("/inbox")).json() if i["run_id"] == run["id"])

    resp = await client.post(f"/inbox/{item['id']}/respond", json={"action": "reject"})
    assert resp.json()["status"] == "completed"  # the run still finishes
    assert executed["n"] == 0  # the tool was never executed
