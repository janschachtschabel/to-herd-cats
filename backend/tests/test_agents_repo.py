"""Repository-level tests: Agent persists and round-trips through the DB."""

from app.models.agent import Agent
from app.repositories.agents import SqlAlchemyAgentRepository


async def test_add_and_get_agent(db_session):
    repo = SqlAlchemyAgentRepository(db_session)
    agent = Agent(name="Researcher", role="analyst", goal="summarise sources")
    await repo.add(agent)
    await db_session.commit()

    fetched = await repo.get(agent.id)
    assert fetched is not None
    assert fetched.name == "Researcher"
    assert fetched.status == "draft"
    assert fetched.tool_ids == []
    assert fetched.skill_ids == []


async def test_list_and_delete(db_session):
    repo = SqlAlchemyAgentRepository(db_session)
    await repo.add(Agent(name="A"))
    await repo.add(Agent(name="B"))
    await db_session.commit()

    assert {a.name for a in await repo.list()} == {"A", "B"}

    target = next(a for a in await repo.list() if a.name == "A")
    await repo.delete(target)
    await db_session.commit()
    assert [a.name for a in await repo.list()] == ["B"]
