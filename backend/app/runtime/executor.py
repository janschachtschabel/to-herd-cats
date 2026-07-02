"""Prompt building for agent runs: the system prompt and initial conversation.

The actual model calls and the tool loop live in runtime/graph.py.
"""

from app.models.agent import Agent


def system_prompt(agent: Agent, skills: str = "") -> str:
    parts = [f"You are {agent.role}." if agent.role else "You are a helpful agent."]
    if agent.goal:
        parts.append(f"Your goal: {agent.goal}")
    if agent.instructions:
        parts.append(agent.instructions)
    # ``skills`` are the enabled skills' instructions (resolved by the caller),
    # appended so the agent follows their procedures.
    if skills:
        parts.append(skills)
    return "\n".join(parts)


def initial_messages(agent: Agent, goal: str, context: str = "", skills: str = "") -> list[dict]:
    # ``context`` carries recalled memory and/or retrieved data-source content;
    # each section is self-labelled by the caller, so the header stays generic.
    messages = [{"role": "system", "content": system_prompt(agent, skills)}]
    if context:
        messages.append(
            {
                "role": "system",
                "content": "Context for this run:\n" + context,
            }
        )
    messages.append({"role": "user", "content": goal})
    return messages
