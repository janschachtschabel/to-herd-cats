"""FastAPI application factory for the Agent Cockpit control API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.agents import router as agents_router
from app.api.health import router as health_router
from app.api.llm_connections import router as llm_connections_router
from app.api.skills import router as skills_router
from app.core.db import make_engine, make_session_factory
from app.core.settings import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the engine and session factory on startup; dispose on shutdown."""
    settings: Settings = app.state.settings
    engine = make_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a configured FastAPI app. Pass ``settings`` to override (tests)."""
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(llm_connections_router)
    app.include_router(skills_router)
    return app


app = create_app()
