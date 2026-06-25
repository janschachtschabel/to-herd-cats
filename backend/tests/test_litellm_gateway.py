"""Tests for the LiteLLM gateway.

These exercise LiteLLM's real ``mock_response`` path (no API key, no network),
so they test the gateway's call-building and normalization against the real
library rather than a hand-rolled mock of it.
"""

import pytest

from app.core.secret_ref import SecretResolutionError
from app.integrations.litellm_gateway import complete
from app.models.llm_connection import LLMConnection


async def test_complete_returns_normalized_result():
    conn = LLMConnection(name="t", provider_model="gpt-4o-mini", params={"temperature": 0.0})
    result = await complete(conn, [{"role": "user", "content": "hi"}], mock_response="Hello!")
    assert result.content == "Hello!"
    assert result.model == "gpt-4o-mini"
    assert result.total_tokens is not None  # LiteLLM fills usage for mocks too


async def test_complete_raises_on_missing_secret(monkeypatch):
    monkeypatch.delenv("THC_MISSING_LLM_KEY", raising=False)
    conn = LLMConnection(
        name="t",
        provider_model="gpt-4o-mini",
        api_key_ref="env:THC_MISSING_LLM_KEY",
    )
    # The SecretRef is resolved before any provider call, so a missing key fails
    # cleanly here instead of leaking into LiteLLM.
    with pytest.raises(SecretResolutionError):
        await complete(conn, [{"role": "user", "content": "hi"}], mock_response="x")


async def test_complete_returns_tool_calls():
    conn = LLMConnection(name="t", provider_model="gpt-4o-mini")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two numbers",
                "parameters": {"type": "object"},
            },
        }
    ]
    mock_tc = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "add", "arguments": '{"a": 2, "b": 3}'},
        }
    ]
    result = await complete(
        conn,
        [{"role": "user", "content": "add 2 and 3"}],
        tools=tools,
        mock_response="",
        mock_tool_calls=mock_tc,
    )
    assert result.tool_calls is not None
    assert result.tool_calls[0]["name"] == "add"
    assert result.tool_calls[0]["arguments"] == {"a": 2, "b": 3}
    assert result.assistant_message["tool_calls"][0]["function"]["name"] == "add"
