"""Autonomous-mode triggers: run an agent in a budget-bounded loop.

Each iteration fires one run; the loop stops when the configured budget is spent
(iterations, cumulative cost, or tokens) or a hard safety cap is reached, with
``interval`` seconds between iterations. The sleep is injectable so the loop is
unit-tested without real waiting.

The natural-language ``stop_condition`` (LLM-judged) is a deliberate follow-up;
budget-based stopping is the concrete mechanism here. Loops run as detached
background tasks (dev-grade): no durable lifecycle or restart yet - that arrives
with durable execution.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.runs import SqlAlchemyRunRepository
from app.triggers.runner import fire

logger = logging.getLogger(__name__)

# Safety net so an autonomous trigger with no budget still terminates.
MAX_AUTONOMOUS_ITERATIONS = 100

Sleep = Callable[[float], Awaitable[None]]


@dataclass
class _Spent:
    iterations: int = 0
    cost: float = 0.0
    tokens: int = 0


def _exhausted(spent: _Spent, budget: dict) -> bool:
    if spent.iterations >= MAX_AUTONOMOUS_ITERATIONS:
        return True
    caps = (("iterations", spent.iterations), ("cost", spent.cost), ("tokens", spent.tokens))
    return any(key in budget and value >= budget[key] for key, value in caps)


async def _run_metrics(factory: async_sessionmaker[AsyncSession], run_id: str) -> dict:
    async with factory() as session:
        run = await SqlAlchemyRunRepository(session).get(run_id)
        return (run.metrics if run else None) or {}


async def run_autonomous(
    factory: async_sessionmaker[AsyncSession],
    agent_id: str,
    trigger_id: str | None,
    loop_config: dict,
    sleep: Sleep = asyncio.sleep,
) -> list[str]:
    """Loop runs for an agent until the budget is spent; return the run ids."""
    budget = loop_config.get("budget") or {}
    interval = loop_config.get("interval") or 0
    spent = _Spent()
    run_ids: list[str] = []
    while True:
        run_id = await fire(factory, agent_id, trigger_id)
        spent.iterations += 1
        if run_id:
            run_ids.append(run_id)
            metrics = await _run_metrics(factory, run_id)
            spent.cost += metrics.get("cost") or 0.0
            spent.tokens += metrics.get("tokens") or 0
        if _exhausted(spent, budget):
            return run_ids
        if interval:
            await sleep(interval)


async def run_autonomous_guarded(
    factory: async_sessionmaker[AsyncSession],
    agent_id: str,
    trigger_id: str | None,
    loop_config: dict,
) -> None:
    """Entry for a detached background task: log failures, never raise."""
    try:
        await run_autonomous(factory, agent_id, trigger_id, loop_config)
    except Exception:
        logger.exception("autonomous loop for trigger %s failed", trigger_id)
