"""Persistent LangGraph checkpointer on a SQLite store (durability).

Replaces the process-lifetime MemorySaver so paused runs (waiting_human) survive
a restart and can still be resumed. SQLite-backed for dev / single-node; the
Postgres saver lands with Postgres parity (M9). Checkpoints live in their own
SQLite file to avoid cross-locking with the app's SQLAlchemy connection.
"""

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.core.settings import Settings


async def open_sqlite_checkpointer(
    path: str,
) -> tuple[AsyncSqliteSaver, aiosqlite.Connection]:
    """Open a persistent saver on ``path`` (creating its tables).

    Returns the saver and its connection; the caller closes the connection on
    shutdown.
    """
    conn = await aiosqlite.connect(path)
    saver = AsyncSqliteSaver(conn)
    await saver.setup()
    return saver, conn


async def open_app_checkpointer(
    settings: Settings,
) -> tuple[AsyncSqliteSaver, aiosqlite.Connection] | None:
    """Open the app's persistent checkpointer, or None to keep the in-memory default.

    Only SQLite app databases get the persistent saver here; the Postgres saver
    arrives with M9 (Postgres parity).
    """
    if not settings.database_url.startswith("sqlite"):
        return None
    return await open_sqlite_checkpointer(settings.checkpoint_path)
