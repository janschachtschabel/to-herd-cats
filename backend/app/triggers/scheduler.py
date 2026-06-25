"""In-process cron scheduler for scheduled-mode triggers (single-node dev).

A background task ticks every ``TICK_SECONDS``; each tick, ``run_due`` fires the
triggers whose cron is due and stamps their ``last_fired_at``. The due decision
(``due_triggers``) is pure and clock-injected, so it is unit-tested without the
loop. A durable distributed scheduler (Hatchet/Temporal) is a deliberate
follow-up; this covers dev and single-node deployments.
"""

import asyncio
import logging
from datetime import UTC, datetime

from croniter import CroniterBadCronError, croniter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models._base import utcnow
from app.models.trigger import Trigger
from app.repositories.triggers import SqlAlchemyTriggerRepository
from app.triggers.runner import fire

logger = logging.getLogger(__name__)

TICK_SECONDS = 30


def _as_utc(dt: datetime) -> datetime:
    # SQLite returns DateTime(timezone=True) values tz-naive; we store UTC, so
    # attach UTC to compare safely against the tz-aware scheduler clock.
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _is_due(trigger: Trigger, now: datetime) -> bool:
    # Base the next-fire calculation on the last fire, or the trigger's creation
    # if it has never fired. A bad cron disables this trigger, not the scheduler.
    base = trigger.last_fired_at or trigger.created_at
    if not trigger.cron or base is None:
        return False
    try:
        next_fire = croniter(trigger.cron, _as_utc(base)).get_next(datetime)
    except CroniterBadCronError:
        logger.warning("trigger %s has an invalid cron %r; skipping", trigger.id, trigger.cron)
        return False
    return next_fire <= _as_utc(now)


def due_triggers(triggers: list[Trigger], now: datetime) -> list[Trigger]:
    """Enabled scheduled triggers whose next cron time has arrived by ``now``."""
    return [t for t in triggers if t.enabled and t.mode == "scheduled" and _is_due(t, now)]


async def run_due(factory: async_sessionmaker[AsyncSession], now: datetime) -> int:
    """One scheduler tick: fire due triggers, stamp ``last_fired_at``.

    Returns the number fired. The read session is released before firing so we
    never hold a read transaction open across the per-fire write sessions, which
    SQLite would reject. A failing fire is logged but neither aborts the tick nor
    skips stamping - an unstamped trigger would otherwise re-fire every tick.
    """
    async with factory() as session:
        triggers = await SqlAlchemyTriggerRepository(session).list()
        due = [(t.agent_id, t.id) for t in due_triggers(triggers, now)]

    for agent_id, trigger_id in due:
        try:
            await fire(factory, agent_id, trigger_id)
        except Exception:
            logger.exception("scheduled fire failed for trigger %s", trigger_id)

    if due:
        async with factory() as session:
            repo = SqlAlchemyTriggerRepository(session)
            for _, trigger_id in due:
                trigger = await repo.get(trigger_id)
                if trigger is not None:
                    trigger.last_fired_at = now
            await session.commit()
    return len(due)


async def _loop(factory: async_sessionmaker[AsyncSession]) -> None:
    while True:
        try:
            await run_due(factory, utcnow())
        except Exception:  # a single bad tick must not kill the scheduler
            logger.exception("scheduler tick failed")
        await asyncio.sleep(TICK_SECONDS)


def start(factory: async_sessionmaker[AsyncSession]) -> asyncio.Task:
    """Start the background scheduler loop; return the task to cancel on shutdown."""
    return asyncio.create_task(_loop(factory))
