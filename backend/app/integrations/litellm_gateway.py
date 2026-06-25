"""LiteLLM gateway: turn an LLMConnection into a normalized completion call.

A pure adapter - no DB, no HTTP. It resolves the connection's SecretRef key at
call time (the plaintext key is never stored or logged), forwards the provider
model, params and any tools to LiteLLM, and normalizes the result (content and,
when the model asks to use tools, the tool calls).
"""

import json
import logging

import litellm
from pydantic import BaseModel

from app.core.secret_ref import resolve_secret
from app.models.llm_connection import LLMConnection

logger = logging.getLogger(__name__)

# Embedding model for long-term memory recall; independent of the chat model.
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


class CompletionResult(BaseModel):
    content: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost: float | None = None
    # Set when the model asked to call tools: [{id, name, arguments(dict)}].
    tool_calls: list[dict] | None = None
    # The raw assistant turn (OpenAI shape), to append back into the conversation.
    assistant_message: dict | None = None


async def complete(
    connection: LLMConnection,
    messages: list[dict],
    tools: list[dict] | None = None,
    **overrides: object,
) -> CompletionResult:
    """Run a completion for ``connection`` and return a normalized result.

    ``tools`` (OpenAI function-calling schemas) let the model request tool calls.
    ``overrides`` are forwarded to LiteLLM - e.g. a per-run ``temperature``, or
    ``mock_response`` in tests. The API key is resolved from the connection's
    SecretRef only here, at call time.
    """
    api_key = resolve_secret(connection.api_key_ref) if connection.api_key_ref else None
    params = {k: v for k, v in (connection.params or {}).items() if v is not None}
    params.update(overrides)
    if tools:
        params["tools"] = tools

    response = await litellm.acompletion(
        model=connection.provider_model,
        messages=messages,
        api_base=connection.api_base or None,
        api_key=api_key,
        **params,
    )
    return _normalize(response)


async def embed(
    connection: LLMConnection,
    text: str,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[float]:
    """Embed ``text`` into a vector for semantic memory recall.

    Uses the connection's resolved SecretRef key (same handling as ``complete``).
    The embedding model is independent of the chat model, so it is a separate
    argument defaulting to a small, widely-available model.
    """
    api_key = resolve_secret(connection.api_key_ref) if connection.api_key_ref else None
    response = await litellm.aembedding(
        model=model,
        input=[text],
        api_base=connection.api_base or None,
        api_key=api_key,
    )
    item = response.data[0]
    return item["embedding"] if isinstance(item, dict) else item.embedding


def _normalize(response: object) -> CompletionResult:
    message = response.choices[0].message
    usage = getattr(response, "usage", None)
    # Cost is best-effort: completion_cost cannot price every model (mock or
    # unknown providers); a missing price must not fail the completion.
    try:
        cost = litellm.completion_cost(completion_response=response)
    except Exception:
        cost = None
    tool_calls, assistant_message = _extract_tool_calls(message)
    return CompletionResult(
        content=message.content or "",
        model=response.model,
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
        cost=cost,
        tool_calls=tool_calls,
        assistant_message=assistant_message,
    )


def _extract_tool_calls(
    message: object,
) -> tuple[list[dict] | None, dict | None]:
    raw = getattr(message, "tool_calls", None)
    if not raw:
        return None, None
    normalized: list[dict] = []
    openai_calls: list[dict] = []
    for tc in raw:
        try:
            arguments = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            logger.warning("unparseable tool-call arguments for %s; using {}", tc.function.name)
            arguments = {}
        normalized.append({"id": tc.id, "name": tc.function.name, "arguments": arguments})
        openai_calls.append(
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
        )
    assistant_message = {
        "role": "assistant",
        "content": message.content,
        "tool_calls": openai_calls,
    }
    return normalized, assistant_message
