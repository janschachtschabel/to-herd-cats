# to-herd-cats

> A vendor-neutral, open-source **control plane ("cockpit") for AI agents** —
> create, configure, run and monitor agents the way you'd manage staff.

Herding cats is the art of coordinating many independent, hard-to-steer things.
This project is a single cockpit where a non-technical user defines AI agents
("employees") with a role, a goal, an LLM, tools and data sources, then runs them
on demand, on a schedule, on events, or autonomously. Agents work in the
background and post their results, questions and approval requests into a
**postbox** for human-in-the-loop review.

Everything is pluggable; nothing is monolithic. Tools, data sources and channels
are connected at runtime through an **MCP gateway** — never hard-wired — which is
what keeps the system modular and vendor-neutral.

> **Status:** early scaffolding. This repository currently holds the project
> brief ([`CLAUDE.md`](CLAUDE.md)); concrete schemas, migrations and code follow.

## What it does

- **Agent lifecycle** — create, configure, enable/disable and monitor agents;
  define role, goal, instructions and guardrails (which actions need approval).
- **Tools & data via MCP** — register MCP servers, auto-discover their tools, and
  connect vector / graph / relational / document / wiki data sources. Any plain
  REST API can be wrapped as a virtual MCP endpoint.
- **Any LLM** — register LLM connections through a single gateway (LiteLLM) with
  defaults, limits and cost tracking.
- **Four run modes** — on demand, scheduled (cron), event-driven, or autonomous.
- **Postbox (human-in-the-loop)** — agents post results, questions and approval
  requests; a human accepts / edits / responds / ignores, and the run resumes.
- **Structured output** — reusable templates render reports, research write-ups
  and comparisons from typed, schema-constrained agent output.

## Architecture

Three planes, each a separate module with a clean API/MCP boundary:

- **Control plane** — cockpit UI + control API + domain model (system-of-record)
- **Execution plane** — agent runtime + durable-execution / trigger layer
- **Tool/data plane** — MCP gateway + LLM gateway + data stores

Cross-cutting concerns: Auth/RBAC and Observability.

## Tech stack (all open source)

| Area | Choice |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) + Alembic, `uv` |
| Agent runtime | LangGraph (`interrupt()` for human-in-the-loop / postbox) |
| LLM gateway | LiteLLM (one endpoint, virtual keys, cost tracking) |
| MCP gateway | MCPJungle; ContextForge to wrap REST/gRPC as MCP |
| Persistence | SQLite + sqlite-vec (single node) · PostgreSQL + pgvector (cluster) |
| Frontend | Angular 22 (zoneless, signals-first, standalone), Angular Material 3 |
| Observability | Langfuse + OpenTelemetry |
| Auth | Keycloak (OIDC) |

See [`CLAUDE.md`](CLAUDE.md) for the full brief, domain model and hard rules.

## Repository layout

```
backend/    # FastAPI control API, services, repositories, LangGraph runtime
frontend/   # Angular 22 cockpit UI + embeddable Web Components
infra/      # docker-compose (SQLite default; --profile postgres for cluster)
```

## Development

```bash
docker compose up                              # full stack
uv run uvicorn app.main:app --reload           # backend dev
uv run alembic upgrade head                    # migrations
ng serve                                        # frontend dev
uv run pytest        # backend tests
ng test              # frontend tests (Vitest)
```

## License

Licensed under the [Apache License 2.0](LICENSE) © 2026 Jan Schachtschabel.
