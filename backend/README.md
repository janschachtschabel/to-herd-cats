# to-herd-cats — backend

FastAPI control-plane API for the Agent Cockpit. See the project brief in
[`../CLAUDE.md`](../CLAUDE.md).

## Develop

```bash
uv sync                                   # create venv + install deps
uv run uvicorn app.main:app --reload      # dev server (http://127.0.0.1:8000)
uv run alembic upgrade head               # apply migrations
uv run pytest -q                          # tests
```

Default persistence is SQLite (`cockpit.db`); set `COCKPIT_DATABASE_URL` to a
`postgresql+asyncpg://...` URL to run against PostgreSQL. The switch is
connection-string only — no engine-specific code outside the repositories.
