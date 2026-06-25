"""LiteLLM gateway: turn an LLMConnection into a normalized completion call.

A pure adapter — no DB, no HTTP. It resolves the connection's SecretRef key at
call time (the plaintext key is never stored or logged), forwards the provider
model and params to LiteLLM, and normalizes the result.
"""

import litellm
from pydantic import BaseModel

from app.core.secret_ref import resolve_secret
from app.models.llm_connection import LLMConnection


class CompletionResult(BaseModel):
    content: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost: float | None = None


async def complete(
    connection: LLMConnection,
    messages: list[dict],
    **overrides: object,
) -> CompletionResult:
    """Run a completion for ``connection`` and return a normalized result.

    ``overrides`` are forwarded to LiteLLM — e.g. a per-run ``temperature``, or
    ``mock_response`` in tests. The API key is resolved from the connection's
    SecretRef only here, at call time.
    """
    api_key = resolve_secret(connection.api_key_ref) if connection.api_key_ref else None
    params = {k: v for k, v in (connection.params or {}).items() if v is not None}
    params.update(overrides)

    response = await litellm.acompletion(
        model=connection.provider_model,
        messages=messages,
        api_base=connection.api_base or None,
        api_key=api_key,
        **params,
    )
    return _normalize(response)


def _normalize(response: object) -> CompletionResult:
    usage = getattr(response, "usage", None)
    # Cost is best-effort: completion_cost cannot price every model (mock or
    # unknown providers); a missing price must not fail the completion.
    try:
        cost = litellm.completion_cost(completion_response=response)
    except Exception:
        cost = None
    return CompletionResult(
        content=response.choices[0].message.content or "",
        model=response.model,
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
        cost=cost,
    )
