"""End-to-end tests for structured output + rendering (M4.4a).

The agent's draft (graph.complete) and the structuring call (structured.complete)
are stubbed; the test verifies that with a template the run yields typed JSON in
result plus a rendered output, and without one it keeps the plain answer.
"""

from app.integrations.litellm_gateway import CompletionResult


async def _llm(client) -> str:
    return (
        await client.post(
            "/llm-connections",
            json={"name": "c", "provider_model": "openai/gpt-4o-mini"},
        )
    ).json()["id"]


async def test_run_with_template_structures_and_renders(client, monkeypatch):
    tmpl = (
        await client.post(
            "/templates",
            json={
                "name": "Report",
                "kind": "report",
                "output_schema": {
                    "type": "object",
                    "properties": {"summary": {"type": "string"}},
                },
                "render_template": "# Report\n{{ summary }}",
                "format": "markdown",
            },
        )
    ).json()
    conn_id = await _llm(client)
    agent = (
        await client.post(
            "/agents",
            json={
                "name": "A",
                "llm_connection_id": conn_id,
                "default_template_id": tmpl["id"],
            },
        )
    ).json()

    async def fake_graph_complete(connection, messages, tools=None, **kw):
        return CompletionResult(content="The project is on track.", model="mock", total_tokens=5)

    async def fake_struct_complete(connection, messages, **kw):
        return CompletionResult(content='{"summary": "On track."}', model="mock", total_tokens=3)

    monkeypatch.setattr("app.runtime.graph.complete", fake_graph_complete)
    monkeypatch.setattr("app.runtime.structured.complete", fake_struct_complete)

    run = (await client.post(f"/agents/{agent['id']}/runs", json={"goal": "status"})).json()
    assert run["status"] == "completed"
    assert run["result"] == {"summary": "On track."}
    assert run["rendered_outputs"][0]["format"] == "markdown"
    assert "On track." in run["rendered_outputs"][0]["content"]


async def test_run_without_template_keeps_plain_content(client, monkeypatch):
    conn_id = await _llm(client)
    agent = (await client.post("/agents", json={"name": "A", "llm_connection_id": conn_id})).json()

    async def fake_graph_complete(connection, messages, tools=None, **kw):
        return CompletionResult(content="plain answer", model="mock", total_tokens=2)

    monkeypatch.setattr("app.runtime.graph.complete", fake_graph_complete)

    run = (await client.post(f"/agents/{agent['id']}/runs", json={"goal": "x"})).json()
    assert run["result"] == {"content": "plain answer"}
    assert run["rendered_outputs"] == []
