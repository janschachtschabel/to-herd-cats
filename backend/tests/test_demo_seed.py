"""Opt-in demo data: seed creates a recognizable set; clear removes only it."""

from app.demo_seed import DEMO_PREFIX, clear_demo, seed_demo
from app.models.agent import Agent
from app.repositories.agents import SqlAlchemyAgentRepository
from app.repositories.llm_connections import SqlAlchemyLLMConnectionRepository


async def _demo_agents(session):
    agents = await SqlAlchemyAgentRepository(session).list()
    return [a for a in agents if a.name.startswith(DEMO_PREFIX)]


async def test_seed_creates_wired_demo_records(db_session):
    added = await seed_demo(db_session)
    assert added == 5

    conns = await SqlAlchemyLLMConnectionRepository(db_session).list()
    demo_conn = next(c for c in conns if c.name.startswith(DEMO_PREFIX))
    demo_agents = await _demo_agents(db_session)
    assert len(demo_agents) == 2
    # The demo agents reference the demo LLM connection.
    assert all(a.llm_connection_id == demo_conn.id for a in demo_agents)


async def test_seed_is_idempotent(db_session):
    await seed_demo(db_session)
    assert await seed_demo(db_session) == 0  # already present -> no-op
    assert len(await _demo_agents(db_session)) == 2  # not duplicated


async def test_clear_removes_only_demo_records(db_session):
    repo = SqlAlchemyAgentRepository(db_session)
    await repo.add(Agent(name="Real Agent"))
    await db_session.commit()

    await seed_demo(db_session)
    removed = await clear_demo(db_session)

    assert removed == 5
    names = [a.name for a in await repo.list()]
    assert "Real Agent" in names  # the user's own data is untouched
    assert not any(n.startswith(DEMO_PREFIX) for n in names)
