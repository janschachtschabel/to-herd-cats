"""Shared FastAPI dependencies."""

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents import AgentService
from app.services.llm_connections import LLMConnectionService


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield an async DB session bound to the app's session factory.

    The factory lives on ``app.state`` (set in the lifespan, or by tests), so
    requests never reach for a module-level global.
    """
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_agent_service(session: AsyncSession = Depends(get_session)) -> AgentService:
    """Build the agent service for a request, bound to its session."""
    return AgentService(session)


def get_llm_connection_service(
    session: AsyncSession = Depends(get_session),
) -> LLMConnectionService:
    """Build the LLM-connection service for a request, bound to its session."""
    return LLMConnectionService(session)
