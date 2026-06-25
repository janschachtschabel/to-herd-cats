"""Shared test fixtures: an isolated SQLite app, an HTTP client, a DB session.

Each test gets a fresh file-backed SQLite database under pytest's ``tmp_path``,
with the schema created from the ORM metadata. The HTTP client speaks to the
ASGI app in-process (no network, no running server).
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.db import Base, make_engine, make_session_factory
from app.core.settings import Settings
from app.main import create_app


@pytest_asyncio.fixture
async def engine(tmp_path):
    db_url = f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}"
    eng = make_engine(db_url)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def client(engine):
    settings = Settings(database_url=engine.url.render_as_string(hide_password=False))
    app = create_app(settings)
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest_asyncio.fixture
async def db_session(engine):
    factory = make_session_factory(engine)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def session_factory(engine):
    """A session factory bound to the test engine (for background-task code)."""
    return make_session_factory(engine)
