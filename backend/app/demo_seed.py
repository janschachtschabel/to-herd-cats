"""Opt-in demo data for trying out the cockpit — NOT loaded automatically.

Creates a small, recognizable example set (one LLM connection, two agents, a
skill, a data source) so the UI isn't empty on first use. Every record's name is
prefixed with ``[demo] `` so it is obvious in the UI and can be removed wholesale
again — by deleting the records, or with ``--clear``.

    uv run python -m app.demo_seed            # add the demo data
    uv run python -m app.demo_seed --clear    # remove it again

Idempotent: re-running ``seed`` while demo data is present is a no-op. Assumes
the schema is migrated (as the app does).
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import make_engine, make_session_factory
from app.core.settings import get_settings
from app.models.agent import Agent
from app.models.data_source import DataSource
from app.models.llm_connection import LLMConnection
from app.models.skill import Skill
from app.repositories.agents import SqlAlchemyAgentRepository
from app.repositories.data_sources import SqlAlchemyDataSourceRepository
from app.repositories.llm_connections import SqlAlchemyLLMConnectionRepository
from app.repositories.skills import SqlAlchemySkillRepository

logger = logging.getLogger(__name__)

# Marker on every demo record's name: visible in the UI and the key `clear` uses.
DEMO_PREFIX = "[demo] "

# Repositories whose rows `clear` scans for the marker (all have a `name`).
_DEMO_REPOS = (
    SqlAlchemyLLMConnectionRepository,
    SqlAlchemyAgentRepository,
    SqlAlchemySkillRepository,
    SqlAlchemyDataSourceRepository,
)


async def seed_demo(session: AsyncSession) -> int:
    """Create the demo records and return how many were added (0 if present)."""
    connections = SqlAlchemyLLMConnectionRepository(session)
    if any(c.name.startswith(DEMO_PREFIX) for c in await connections.list()):
        return 0

    conn = LLMConnection(
        name=f"{DEMO_PREFIX}OpenAI GPT-4o mini",
        provider_model="openai/gpt-4o-mini",
        api_key_ref="env:OPENAI_API_KEY",  # a SecretRef, never a plaintext key
    )
    await connections.add(conn)  # flush assigns conn.id for the agents below

    agents = SqlAlchemyAgentRepository(session)
    await agents.add(
        Agent(
            name=f"{DEMO_PREFIX}Rechercheur",
            role="Analyst",
            goal="Recherchiere ein Thema und fasse die wichtigsten Quellen zusammen.",
            llm_connection_id=conn.id,
            status="active",
        )
    )
    await agents.add(
        Agent(
            name=f"{DEMO_PREFIX}Autor",
            role="Redakteur",
            goal="Schreibe aus Stichpunkten einen kurzen, klaren Bericht.",
            llm_connection_id=conn.id,
            status="draft",
        )
    )
    await SqlAlchemySkillRepository(session).add(
        Skill(
            name=f"{DEMO_PREFIX}Zusammenfassen",
            description="Fasst lange Texte in wenige Stichpunkte zusammen.",
            instructions=(
                "# Zusammenfassen\n\n"
                "Fasse den gegebenen Text in höchstens fünf prägnante Stichpunkte "
                "zusammen. Behalte zentrale Fachbegriffe bei."
            ),
        )
    )
    await SqlAlchemyDataSourceRepository(session).add(
        DataSource(name=f"{DEMO_PREFIX}Projekt-Wiki", kind="wiki")
    )
    await session.commit()
    logger.info("seeded demo data")
    return 5


async def clear_demo(session: AsyncSession) -> int:
    """Delete every ``[demo] `` record across the demo entities; return the count."""
    removed = 0
    for repo_cls in _DEMO_REPOS:
        repo = repo_cls(session)
        for entity in await repo.list():
            if entity.name.startswith(DEMO_PREFIX):
                await repo.delete(entity)
                removed += 1
    await session.commit()
    if removed:
        logger.info("cleared %d demo records", removed)
    return removed


async def _run(clear: bool) -> None:
    engine = make_engine(get_settings().database_url)
    try:
        async with make_session_factory(engine)() as session:
            if clear:
                print(f"removed {await clear_demo(session)} demo records")
            else:
                added = await seed_demo(session)
                print(f"seeded {added} demo records" if added else "demo data already present")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Seed or clear [demo] example data.")
    parser.add_argument(
        "--clear", action="store_true", help="remove the [demo] records instead of creating them"
    )
    asyncio.run(_run(parser.parse_args().clear))
