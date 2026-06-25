"""Cross-run agent memory: recall past interactions, and embed for long-term.

Three modes (Agent.memory.mode) decide what an agent remembers between runs:
- none:  no cross-run memory.
- short: recall the most recent interactions (recency).
- long:  recall the semantically closest interactions (embedding cosine).

Long-term recall scores stored embedding vectors with cosine similarity in
Python rather than a native vector index (sqlite-vec / pgvector). Per-agent
memory counts are small at this stage; a vector index can replace the scan
later behind this same interface.
"""

import math

from app.integrations.litellm_gateway import embed
from app.models.llm_connection import LLMConnection
from app.models.memory import MemoryRecord

RECENT_LIMIT = 5  # short-term: how many recent memories to recall
TOP_K = 3  # long-term: how many closest memories to recall


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors; 0.0 when undefined."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


async def embedding_for(content: str, mode: str, connection: LLMConnection) -> list[float] | None:
    """Vector to persist alongside a new memory; only long-term mode embeds."""
    if mode == "long":
        return await embed(connection, content)
    return None


async def recall(
    memories: list[MemoryRecord],
    mode: str,
    query: str,
    connection: LLMConnection,
) -> str:
    """Select relevant past memories for ``query`` and join them into context.

    ``memories`` must be ordered most-recent-first (the repository query does
    this). Returns an empty string when there is nothing to recall.
    """
    if mode == "short":
        chosen = memories[:RECENT_LIMIT]
    elif mode == "long":
        query_vec = await embed(connection, query)
        scored = [(cosine(query_vec, m.embedding), m) for m in memories if m.embedding]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        chosen = [m for _, m in scored[:TOP_K]]
    else:
        return ""
    return "\n\n".join(m.content for m in chosen)
