"""Async database engine, session factory and the declarative base.

The engine is built from a connection string only, so swapping SQLite for
PostgreSQL needs no code change here or in the repositories.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def make_engine(database_url: str) -> AsyncEngine:
    """Create an async engine for the given connection string."""
    return create_async_engine(database_url, future=True)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to ``engine``."""
    return async_sessionmaker(engine, expire_on_commit=False)
