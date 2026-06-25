"""Prompt building for agent runs: the system prompt and initial conversation.

The actual model calls and the tool loop live in runtime/graph.py.
"""

from app.models.agent import Agent


def system_prompt(agent: Agent) -> str:
    parts = [f"You are {agent.role}." if agent.role else "You are a helpful agent."]
    if agent.goal:
        parts.append(f"Your goal: {agent.goal}")
    if agent.instructions:
        parts.append(agent.instructions)
    return "\n".join(parts)


def initial_messages(agent: Agent, goal: str, context: str = "") -> list[dict]:
    messages = [{"role": "system", "content": system_prompt(agent)}]
    if context:
        messages.append(
            {
                "role": "system",
                "content": "Relevant context from your data sources:\n" + context,
            }
        )
    messages.append({"role": "user", "content": goal})
    return messages
