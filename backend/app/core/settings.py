"""Application settings, loaded from the environment with sane defaults.

Secrets are never hard-coded: values come from the environment (prefix
``COCKPIT_``) or an optional ``.env`` file. See CLAUDE.md hard rule 5.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COCKPIT_", env_file=".env", extra="ignore")

    app_name: str = "to-herd-cats"
    debug: bool = False

    # Async SQLAlchemy URL. SQLite (a local file) is the zero-ops default; swap
    # for ``postgresql+asyncpg://...`` to run against a cluster DB. The switch is
    # connection-string only — no engine-specific code outside the repositories.
    database_url: str = "sqlite+aiosqlite:///./cockpit.db"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
