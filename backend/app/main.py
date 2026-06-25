"""FastAPI application factory for the Agent Cockpit control API."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.agents import router as agents_router
from app.api.channels import router as channels_router
from app.api.data_sources import router as data_sources_router
from app.api.health import router as health_router
from app.api.inbox import router as inbox_router
from app.api.llm_connections import router as llm_connections_router
from app.api.mcp_servers import router as mcp_servers_router
from app.api.roles import router as roles_router
from app.api.runs import router as runs_router
from app.api.settings import router as settings_router
from app.api.skills import router as skills_router
from app.api.templates import router as templates_router
from app.api.tools import router as tools_router
from app.api.triggers import router as triggers_router
from app.core.db import make_engine, make_session_factory
from app.core.settings import Settings, get_settings
from app.triggers.scheduler import start as start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build engine + session factory and start the scheduler; clean up on exit."""
    settings: Settings = app.state.settings
    engine = make_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    scheduler_task = start_scheduler(app.state.session_factory)
    try:
        yield
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a configured FastAPI app. Pass ``settings`` to override (tests)."""
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    # Strong refs to detached background tasks (autonomous loops) so the event
    # loop does not garbage-collect them mid-flight.
    app.state.background_tasks = set()
    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(llm_connections_router)
    app.include_router(skills_router)
    app.include_router(mcp_servers_router)
    app.include_router(tools_router)
    app.include_router(data_sources_router)
    app.include_router(templates_router)
    app.include_router(channels_router)
    app.include_router(triggers_router)
    app.include_router(roles_router)
    app.include_router(settings_router)
    app.include_router(runs_router)
    app.include_router(inbox_router)
    return app


app = create_app()
