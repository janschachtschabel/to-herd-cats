"""Event-mode triggers: fire agent runs when a matching event is published.

Dispatch is in-process (single-node dev). A trigger matches an event when its
``event_source`` equals the event's source and its ``event_filter`` is a subset
of the event payload (an empty filter matches any event from that source). A
durable event bus (Redis Streams) behind this same interface is a follow-up;
so is injecting the event payload into the fired run's prompt.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.trigger import Trigger
from app.repositories.triggers import SqlAlchemyTriggerRepository
from app.triggers.runner import fire


def _filter_matches(event_filter: dict, payload: dict) -> bool:
    return all(payload.get(key) == value for key, value in event_filter.items())


def event_targets(triggers: list[Trigger], source: str, payload: dict) -> list[Trigger]:
    """Enabled event-mode triggers whose source and filter match the event."""
    return [
        t
        for t in triggers
        if t.enabled
        and t.mode == "event"
        and t.event_source == source
        and _filter_matches(t.event_filter or {}, payload)
    ]


async def dispatch(
    factory: async_sessionmaker[AsyncSession], source: str, payload: dict
) -> list[str]:
    """Fire every matching event-trigger for one event; return the run ids.

    The read session is released before firing so we never hold a read
    transaction open across the per-fire write sessions (SQLite).
    """
    async with factory() as session:
        triggers = await SqlAlchemyTriggerRepository(session).list()
        targets = [(t.agent_id, t.id) for t in event_targets(triggers, source, payload)]

    run_ids: list[str] = []
    for agent_id, trigger_id in targets:
        run_id = await fire(factory, agent_id, trigger_id)
        if run_id:
            run_ids.append(run_id)
    return run_ids
