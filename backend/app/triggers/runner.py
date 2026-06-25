"""Fire a single agent run from a trigger, in its own DB session.

Triggers fire outside any HTTP request (a scheduler tick, the autonomous loop,
event dispatch), so each fire opens a fresh session from the app's session
factory and drives the same RunService that on-demand runs use.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.agents import SqlAlchemyAgentRepository
from app.schemas.run import RunInput
from app.services.runs import RunService

# Fallback goal when an agent has no configured goal of its own.
DEFAULT_GOAL = "Proceed with your configured task."


async def fire(
    factory: async_sessionmaker[AsyncSession],
    agent_id: str,
    trigger_id: str | None = None,
) -> str | None:
    """Execute one run for ``agent_id``; return the run id, or None if no agent.

    The goal defaults to the agent's configured goal, so scheduled and autonomous
    runs need no per-fire input. ``trigger_id`` is recorded on the resulting run.
    """
    async with factory() as session:
        agent = await SqlAlchemyAgentRepository(session).get(agent_id)
        if agent is None:
            return None
        payload = RunInput(goal=agent.goal or DEFAULT_GOAL)
        run = await RunService(session).create_and_execute(agent_id, payload, trigger_id=trigger_id)
        return run.id
