"""Execute an agent as a single LLM completion (M4.1).

Builds the agent's system prompt from its definition plus the run goal, then
calls the LiteLLM gateway. Multi-step graphs, tools, retrieval and memory arrive
in later M4 sub-increments.
"""

from app.integrations.litellm_gateway import CompletionResult, complete
from app.models.agent import Agent
from app.models.llm_connection import LLMConnection


def _system_prompt(agent: Agent) -> str:
    parts = [f"You are {agent.role}." if agent.role else "You are a helpful agent."]
    if agent.goal:
        parts.append(f"Your goal: {agent.goal}")
    if agent.instructions:
        parts.append(agent.instructions)
    return "\n".join(parts)


async def run_agent(agent: Agent, connection: LLMConnection, run_input: dict) -> CompletionResult:
    """Run the agent for one turn and return the normalized completion."""
    messages = [
        {"role": "system", "content": _system_prompt(agent)},
        {"role": "user", "content": run_input.get("goal", "")},
    ]
    return await complete(connection, messages)
