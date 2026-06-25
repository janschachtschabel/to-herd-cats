# Implementation Plan — to-herd-cats (Agent Cockpit)

> **What this is.** The execution roadmap: build strategy, milestones (M0–M9),
> open decisions, scope boundaries and a progress log.
> [`CLAUDE.md`](../CLAUDE.md) is the **contract** (what to build — purpose, tech
> stack, domain model, hard rules); this document is the **sequence** (how and in
> what order). Keep both in sync.
>
> **Status (2026-06-25): M0–M3 complete and verified.** 63 tests green; Alembic
> migrations `0001–0007` apply from scratch with no model drift; backend is
> ruff-clean; pushed to `origin/main`. **Next: M4.**

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

### ✅ M3 — Integrations layer (the seam) — DONE
- **Goal:** the LLM and tool wiring made real.
- **Built:** `integrations/litellm_gateway.py` (resolve an LLMConnection's
  SecretRef key at call time → LiteLLM call → normalized result: content, model,
  usage, best-effort cost). `integrations/mcp_gateway.py` (connect to an
  MCPServer over stdio / streamable HTTP, list tools → normalized descriptors).
  `POST /mcp-servers/{id}/discover` caches `discovered_tools` and sets status
  connected/error. `config_schema` is stored on MCPServer (since M2); the form
  renders it in M7. New deps: `litellm`, `mcp` (official SDK).
- **Decisions/limits:** discovery connects *directly* to each server; MCPJungle
  routing and authenticated discovery (resolving `credentials_ref` to headers)
  are deferred. ContextForge (REST→MCP) deferred until needed.
- **Verified:** 63 tests; the LiteLLM gateway via LiteLLM's real `mock_response`
  path and MCP discovery against a real in-memory FastMCP server (not
  self-mocks); backend is ruff-clean.

### M4 — Execution plane: runtime + Run + Postbox (the heart) — DONE
- **Status:** ✅ M4.1 runs · ✅ M4.2 postbox · ✅ M4.3 tool use · ✅ M4.4 structured
  output · ✅ M4.5 retrieval · ✅ M4.6 memory — M4 complete.
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
- **Data & retrieval:** the runtime also queries the agent's **data sources**
  (vector/graph/wiki/relational) for grounding — the knowledge-grounded scenario
  (CLAUDE.md §2). Data sources reach the runtime via MCP or a thin driver adapter.
- **Agent memory:** ✅ cross-run recall keyed by `Agent.memory.mode`
  (none / short / long). Short = the most recent interactions (recency); long =
  the semantically closest, via embeddings (`litellm.aembedding`) scored by
  cosine similarity. A completed run is stored as a `MemoryRecord` (goal +
  answer; embedded for long mode) and recalled into the next run's context.
  **Deviation:** embeddings are stored as JSON and scored in Python rather than
  with a native `sqlite-vec` / `pgvector` index — no native extension needed, and
  per-agent memory counts are small at this stage; a vector index can replace the
  scan behind the `runtime/memory.py` interface later. The embedding model is a
  module default (`text-embedding-3-small`) and `Agent.memory.vector_store_ref`
  remains a placeholder for an external store — both are follow-ups.
- **Note:** `Run` and `InboxItem` are new entities here (new migration). M4 is the
  largest milestone — deliver it in sub-increments (runtime → postbox → structured
  output → retrieval → memory), verifying each.
- **Verify:** end-to-end run with a mock LLM; an interrupt/resume cycle; a
  rendered report from typed JSON; a retrieval-grounded answer; long-term memory
  recall across two runs.

### M4b — Executable skills (sandboxed) — security-hardened
- **Goal:** run a skill's bundled scripts safely.
- **Plan:** isolated, least-privilege sandbox (restricted subprocess / container)
  for skill scripts; no host FS/network beyond declared `scopes`; execution is
  approval-gateable via the postbox and audited (CLAUDE.md §9.11). Deliberately
  separate from M4 so the core does not block on the sandbox.
- **Verify:** a script runs inside the sandbox; an out-of-scope action is denied;
  an approval gate pauses execution.

### M5 — Triggers & durability — IN PROGRESS
- **Status:** ✅ M5.1 scheduled (in-process cron); remaining: M5.2 autonomous ·
  M5.3 event · M5.4 durable checkpointer.
- **Goal:** all four run modes (CLAUDE.md §3).
- **Plan:** `triggers/` in-process scheduler (dev, cron) + event handlers +
  **pluggable** durable-execution adapter interface (Hatchet/Temporal optional;
  dev runs without it); scheduled + event + autonomous (loop with
  budget/stop-condition); event bus (Redis Streams) behind an interface.
- **Verify:** a cron-scheduled run fires (mocked clock); an event trigger; an
  autonomous loop stops on its condition.

### M6 — Observability
- **Goal:** visibility into cost/tokens/traces, plus outbound delivery of postbox
  items to channels.
- **Plan:** `integrations/langfuse` + OpenTelemetry; `Run.metrics`
  (tokens/cost/duration) + `trace_id`.
- **Channel delivery:** when an `InboxItem` carries `channel_ids`, route it to
  those Channels (Slack/email/webhook/matrix, via MCP or a thin adapter). Channel
  *config* is already M2; this adds the *delivery* behaviour (CLAUDE.md §3,
  "routing of postbox items to channels"). Start with one kind, extend by adapter.
- **Verify:** a trace/metric is produced (mock/local Langfuse); an `InboxItem` is
  delivered to a mock channel.

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

## Cross-cutting concerns (span milestones)

- **CI pipeline.** GitHub Actions on push/PR: `ruff check` + `ruff format
  --check` + `uv run pytest` for the backend, and `ng test` + `ng build` once the
  frontend exists. Set up early so "green by default" holds; gate merges on it.
- **API error model.** One consistent error shape; map domain errors and
  `IntegrityError` (e.g. a bad foreign key) to a clean 4xx, never a 500 with a
  stack trace (CLAUDE.md §11). Subsumes the bad-FK follow-up below.
- **CORS.** Allowed-origins config for the Angular SPA → API (needed from M7);
  keep it tight and env-driven.
- **Security review pass.** Route auth, secret handling, skill execution (M4b)
  and input boundaries through an extra review before "done" (CLAUDE.md §11).
- **Audit trail.** Entities already carry created/updated timestamps; add
  who-did-what for sensitive actions (approvals, role changes) when auth lands
  (M8).
- **Dev infrastructure.** `infra/docker-compose.yml` grows by milestone — Postgres
  (parity), Redis (M5 events), Langfuse (M6), Keycloak (M8) — not only at M9.

## Testing approach

- **Pyramid per entity:** repository tests (real tmp SQLite) → service tests →
  API tests (httpx against the ASGI app, no network) → runtime tests (mock LLM,
  deterministic). Frontend: Vitest component tests.
- **External services mocked** in unit tests (LiteLLM, MCP, Langfuse, Keycloak);
  one optional integration test each against a real local instance.
- **Isolation:** each test gets a fresh tmp SQLite DB with the schema created from
  ORM metadata; `alembic check` guards against model/migration drift.
- **Both backends:** the suite must pass on SQLite and (M9 / CI) PostgreSQL.
- **Pin behaviour before implementing** where feasible; never weaken a test to go
  green (CLAUDE.md §9.10).

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
| 2026-06-25 | docs: implementation plan + review/refinement | `4e82a19`, `891eb5a` |
| 2026-06-25 | M3: LiteLLM gateway + ruff config & lint/format pass | `a0e2717` |
| 2026-06-25 | M3: MCP tool-discovery gateway | `f1bb7d9` |
| 2026-06-25 | M3: discover endpoint completes M3 | `5864999` |
| 2026-06-25 | M4.1: on-demand Run execution | `1518734` |
| 2026-06-25 | M4.2: LangGraph postbox (HITL interrupt/resume) | `e1b278b` |
| 2026-06-25 | M4.3a-i: tool plumbing (gateway tools, MCP call_tool) | `c1e5c36` |
| 2026-06-25 | M4.3a-ii: agent<->tools loop | `b41726c` |
| 2026-06-25 | M4.3b: per-tool approval gate | `9994988` |
| 2026-06-25 | M4.4a: structured output + Jinja2 render | `702da67` |
| 2026-06-25 | M4.4b: run comparison | `a823d2b` |
| 2026-06-25 | M4.5: data-source retrieval (RAG) | `b202074` |
| 2026-06-25 | M4.6: agent memory (cross-run recall) — completes M4 | `525393d` |
| 2026-06-25 | M5.1: cron scheduler (scheduled-mode triggers) | `a68f9ac` |
