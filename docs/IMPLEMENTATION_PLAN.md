# Implementation Plan — to-herd-cats (Agent Cockpit)

> **What this is.** The execution roadmap: build strategy, milestones (M0–M9),
> open decisions, scope boundaries and a progress log.
> [`CLAUDE.md`](../CLAUDE.md) is the **contract** (what to build — purpose, tech
> stack, domain model, hard rules); this document is the **sequence** (how and in
> what order). Keep both in sync.
>
> **Status (2026-06-25): M0–M2 complete and verified.** 54 tests green; Alembic
> migrations `0001–0007` apply from scratch with no model drift; pushed to
> `origin/main`. **Next: M3.**

## Working agreements

- **Vertical slice first**, not layer-by-layer: take one entity end-to-end and
  reuse it as the template.
- **Evidence-based verification**: each milestone ends with a real command +
  output (no "should work").
- **Small, traceable diffs**, auto-pushed per verified increment to
  `origin/main`.
- **Invoke the `better-coding-workflow` skill before starting each new
  milestone.**
- **File size** target ≤300 / hard ≤400 lines; one responsibility per file
  (CLAUDE.md §9.1).
- **SQLite default, Postgres parity** by construction — connection-string only,
  no engine-specific code outside repositories.

## Build strategy (guiding principles)

1. **Vertical slice first.** One entity through every layer (router → service →
   repository → migration → tests) becomes the copyable template, so the core is
   runnable early and the pattern is fixed before it multiplies.
2. **MCP is the seam.** Tools, data sources, channels and foreign agents are
   registered at runtime through the MCP gateway, never hard-wired (CLAUDE.md
   §2, §10). Skills are the second capability axis (procedural know-how).
3. **SQLite default, Postgres parity from day one.** All persistence sits behind
   repository interfaces; switching is connection-string only and is tested in
   every milestone, not retrofitted at the end.
4. **Every milestone ends with evidence**, not "looks done": a green test run
   plus a shown command output. No merge without a test (CLAUDE.md §9.10, §12).
5. **One bounded module per domain area; small files.** Each entity gets its own
   files per layer.

## Milestones

### ✅ M0 — Runnable skeleton — DONE
- **Goal:** an empty but starting, testable backend.
- **Built:** `backend/` (uv); FastAPI app factory + lifespan-managed async
  SQLAlchemy; `core/settings` (pydantic-settings) + `core/db`; async Alembic;
  pytest harness; `/health`.
- **Verified:** `pytest` green; `uvicorn` serves `/health` → `200 {"status":"ok"}`.

### ✅ M1 — Domain core + Agent vertical slice — DONE
- **Goal:** `Agent` end-to-end + the reusable layer template.
- **Built:** `models/agent` ↔ `schemas/agent` (separate), `repositories/agents`,
  `services/agents`, thin `api/agents`; first Alembic migration. This is the
  **router → service → repository** template every other entity follows.
- **Verified:** repository/service/API tests green; CRUD over HTTP; migration on
  SQLite.

### ✅ M2 — Remaining configuration entities — DONE
- **Goal:** everything "create & configure" from CLAUDE.md §3 as data.
- **Built:** all 11 domain entities (CLAUDE.md §7) with full CRUD — Agent,
  LLMConnection, Skill, MCPServer, Tool, DataSource, Template, Channel, Trigger,
  Role, Setting. Shared foundation extracted once it was justified by real
  cases: `UuidAuditMixin`, `BaseRepository[Model]`, `CrudService`, a shared
  `SecretRefField`, and SQLite FK enforcement. First foreign keys
  (Tool→MCPServer SET NULL, Trigger→Agent CASCADE). `Setting` is bespoke — a
  scoped `(scope, key)` key/value store with upsert (PUT) instead of generic
  CRUD. Credentials are stored only as SecretRefs (`env:VAR`), never plaintext.
- **Verified:** 54 tests; full migration chain `0001–0007` applies from scratch;
  `alembic check` reports no model/migration drift; 11 entity tables created.

### M3 — Integrations layer (the seam)
- **Goal:** the LLM and tool wiring made real.
- **Plan:** `integrations/litellm` (resolve LLMConnection → call, cost/limits);
  `integrations/mcp_gateway` (MCPJungle: register a server, auto-discover its
  tools → `MCPServer.discovered_tools`); `config_schema` handling (validate /
  store the Smithery-style form schema). IBM ContextForge (REST→MCP) deferred
  until needed.
- **Verify:** tool discovery against a real/mock MCP server → tool list; a
  LiteLLM call against a mock provider.

### M4 — Execution plane: runtime + Run + Postbox (the heart)
- **Goal:** an agent runs, pauses for a human, resumes — the "employee replies"
  mechanism.
- **Plan:** `runtime/` LangGraph graph (uses an LLMConnection + selected tools
  via the gateway); `Run` (repository/service, `thread_id` checkpoint on the app
  DB); `inbox/` `InboxItem` + the `interrupt()` → `waiting_human` → replay →
  resume state machine (CLAUDE.md §8); on-demand runs first; structured-output
  pipeline (Instructor + `Template.output_schema` → `Run.result` → Jinja2 →
  `rendered_outputs`); a comparison = structured diff of two `Run.result`s.
  Also: **skill resolution** in the runtime — match enabled skills by
  `description` (progressive disclosure) and inject; fixed commands invoke a
  skill deterministically.
- **Verify:** end-to-end run with a mock LLM; an interrupt/resume cycle; a
  rendered report from typed JSON.

### M4b — Executable skills (sandboxed) — security-hardened
- **Goal:** run a skill's bundled scripts safely.
- **Plan:** isolated, least-privilege sandbox (restricted subprocess / container)
  for skill scripts; no host FS/network beyond declared `scopes`; execution is
  approval-gateable via the postbox and audited (CLAUDE.md §9.11). Deliberately
  separate from M4 so the core does not block on the sandbox.
- **Verify:** a script runs inside the sandbox; an out-of-scope action is denied;
  an approval gate pauses execution.

### M5 — Triggers & durability
- **Goal:** all four run modes (CLAUDE.md §3).
- **Plan:** `triggers/` in-process scheduler (dev, cron) + event handlers +
  **pluggable** durable-execution adapter interface (Hatchet/Temporal optional;
  dev runs without it); scheduled + event + autonomous (loop with
  budget/stop-condition); event bus (Redis Streams) behind an interface.
- **Verify:** a cron-scheduled run fires (mocked clock); an event trigger; an
  autonomous loop stops on its condition.

### M6 — Observability
- **Goal:** visibility into cost/tokens/traces.
- **Plan:** `integrations/langfuse` + OpenTelemetry; `Run.metrics`
  (tokens/cost/duration) + `trace_id`.
- **Verify:** a trace/metric is produced (asserted against a mock/local Langfuse).

### M7 — Frontend cockpit (Angular 21) + skill authoring
- **Goal:** a usable cockpit for non-programmers (CLAUDE.md §9.8).
- **Plan:** Angular 21 zoneless/signals/standalone + Material 3, Vitest, i18n
  (default `de`); `core/` (API client, interceptors, guards); `features/` CRUD
  masks for every entity; the **generic "add server/source" form rendered from
  `config_schema`**; the **postbox UI** (accept/edit/respond/ignore) built fresh
  in Angular (Agent-Inbox pattern, not a React fork); embeddable Web Components
  via `@angular/elements`; a **skill-authoring UI** (create/validate/test a
  SKILL.md, define commands) plus an **AI skill-creator** — an internal seed
  agent on the cockpit's own runtime that drafts a SKILL.md from a description
  (dogfooding the first built-in agent).
- **Verify:** `ng build` + `ng test` green; UI drives the real API; every UI
  string is an i18n key.

### M8 — Auth & RBAC (Keycloak)
- **Goal:** user management with roles (CLAUDE.md §3 Platform).
- **Plan:** Keycloak (OIDC); the app stores only role→permission mappings and
  ownership; backend dependency guards + frontend route guards; permissions like
  `agent.create`, `run.approve`.
- **Verify:** protected endpoints enforce roles (403 without permission, 200
  with).

### M9 — Postgres parity & packaging
- **Goal:** Definition of Done met (CLAUDE.md §12: runs on SQLite *and* Postgres).
- **Plan:** run the full suite against the `--profile postgres` DB;
  `docker-compose.prod.yml`; sync README / CLAUDE.md / this plan.
- **Verify:** the whole suite green on both DB backends — both outputs shown.

## Open technical decisions & defaults

| Topic | Default | Rationale |
| --- | --- | --- |
| Durable execution (prod) | Interface now, adapter later; **Hatchet** recommended | Simpler ops than Temporal, AI-pipeline focus; dev needs none |
| Auth ordering | Dev stub through M3–M7, **real Keycloak in M8** | Don't block the core on Keycloak setup |
| Postbox UI | **Fresh in Angular** (Agent-Inbox pattern) | Frontend is Angular; a React fork would break the stack |
| LangGraph checkpointer | **App DB** (SQLite/Postgres saver) | One persistence store, no extra service |
| Frontend package manager | **pnpm** | Fast, space-efficient; convention only |
| MCP gateway start | **MCPJungle** first; ContextForge when REST-wrapping is needed | CLAUDE.md §4 default |
| Skill depth | Full schema modelled; **instruction/command skills first**, executable sandbox = M4b | Value early, code-execution risk in a controlled step |
| Skill authoring | Authoring UI **and** an AI skill-creator (M7) | User decision; the creator dogfoods the runtime |

## Scope boundaries (deliberately NOT doing)

No off-the-shelf suites embedded; no forking external UIs; no rebuilding wikis /
graph DBs (connect only); not both durable-exec backends at once; no speculative
integrations "just in case". Per milestone, only what the verification requires.

## Open follow-ups (carried)

- **Postgres parity** not yet run live (local Docker daemon down). Code is
  engine-agnostic by construction; prove it in M9 or sooner.
- **Bad foreign key → 500.** Posting a Tool/Trigger with a non-existent parent id
  returns a generic 500 (unhandled `IntegrityError`) instead of a clean 4xx. Add
  a small generic `IntegrityError` handler (or referential validation) — flagged,
  not yet done.
- **`deps.py` providers.** ~10 near-identical service providers; a candidate to
  factor once it earns its keep.

## Progress log

| When | Increment | Commit |
| --- | --- | --- |
| 2026-06-24 | Repo init: brief, README, Apache-2.0, .gitignore | `2a78efc` |
| 2026-06-24 | M0+M1: FastAPI skeleton + Agent slice; Skills folded into CLAUDE.md | `01f6310` |
| 2026-06-24 | M2: LLMConnection + shared CRUD/SecretRef foundation | `1a625b6` |
| 2026-06-24 | M2: Skill entity + extract generic CrudService | `92b8e9c` |
| 2026-06-24 | M2: MCPServer + Tool, shared SecretRefField, SQLite FK | `75ae3f5` |
| 2026-06-24 | M2: DataSource, Template, Channel | `9d9e684` |
| 2026-06-24 | M2: Trigger + Role | `41d52b2` |
| 2026-06-24 | M2: Setting completes the M2 entities | `76d6afd` |
