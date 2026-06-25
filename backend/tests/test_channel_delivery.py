"""Tests for channel delivery of postbox items (M6.2).

A run that pauses for human approval posts an InboxItem; it is routed to the
enabled outbound channels whose routing matches the item type and delivered via
the channel's MCP 'send' tool (stubbed). Non-matching channels are skipped.
"""

from app.integrations.litellm_gateway import CompletionResult


async def _run_paused_with_channel(client, monkeypatch, *, routing):
    sent = []

    async def fake_call_tool(server, tool_name, arguments):
        sent.append((tool_name, arguments))
        return "ok"

    monkeypatch.setattr("app.channels.delivery.call_tool", fake_call_tool)

    async def fake_complete(connection, messages, tools=None, **kw):
        return CompletionResult(content="draft", model="mock", total_tokens=2)

    monkeypatch.setattr("app.runtime.graph.complete", fake_complete)

    conn = (
        await client.post(
            "/llm-connections", json={"name": "c", "provider_model": "openai/gpt-4o-mini"}
        )
    ).json()
    server = (
        await client.post("/mcp-servers", json={"name": "s", "transport": "stdio", "command": "x"})
    ).json()
    channel = (
        await client.post(
            "/channels",
            json={
                "name": "slack",
                "kind": "slack",
                "mcp_server_id": server["id"],
                "direction": "out",
                "routing": routing,
            },
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
    run = (await client.post(f"/agents/{agent['id']}/runs", json={"goal": "do"})).json()
    return run, channel, sent


async def test_inbox_item_delivered_to_matching_channel(client, monkeypatch):
    run, channel, sent = await _run_paused_with_channel(
        client, monkeypatch, routing=["approval_request"]
    )
    assert run["status"] == "waiting_human"

    assert len(sent) == 1
    tool_name, arguments = sent[0]
    assert tool_name == "send"
    assert arguments["type"] == "approval_request"

    inbox = (await client.get("/inbox")).json()
    assert inbox[0]["channel_ids"] == [channel["id"]]


async def test_channel_not_matching_item_type_is_skipped(client, monkeypatch):
    run, channel, sent = await _run_paused_with_channel(
        client, monkeypatch, routing=["something_else"]
    )
    assert run["status"] == "waiting_human"

    assert sent == []  # routing did not match the item type
    inbox = (await client.get("/inbox")).json()
    assert inbox[0]["channel_ids"] == []
