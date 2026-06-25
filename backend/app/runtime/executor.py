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


def initial_messages(agent: Agent, goal: str) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt(agent)},
        {"role": "user", "content": goal},
    ]
