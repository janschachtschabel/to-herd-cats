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

    # Persistent LangGraph checkpoint store (its own SQLite file to avoid
    # cross-locking with the app DB connection). Used when the app database is
    # SQLite; the Postgres saver arrives with M9.
    checkpoint_path: str = "./cockpit.checkpoints.db"

    # Browser origins allowed to call the API (the Angular dev server). Listed
    # explicitly rather than "*" so credentials can be added safely later.
    cors_origins: list[str] = ["http://localhost:4200"]

    # Authorization dev stub (until Keycloak/OIDC lands). When true, the cockpit
    # is usable without a login: a request with no ``X-Dev-Roles`` header is a
    # wildcard admin, and the header simulates a user's roles. When false the
    # stub is off — every request is anonymous and guarded routes deny by
    # default (the header is not honored). See app/api/security.py.
    auth_dev_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
