# CLAUDE.md — Agent Cockpit

> Working title. A vendor-neutral, open-source control plane ("cockpit") for
> creating, configuring, running and monitoring AI agents — managed like staff.
> Tools and data sources are connected via MCP; agents report back into a
> postbox for human-in-the-loop. Everything is pluggable; nothing monolithic.

This file is the project brief a coding agent starts from. Concrete schemas,
migrations and code are produced by the coding agent; the shapes below are the
agreed contracts. Keep everything modular.

## 1. What the app does

A single cockpit where a user defines AI agents ("employees") with a role, a
goal, an LLM, tools, skills and data sources, then runs them on demand, on a schedule,
on events, or autonomously. Agents work in the background and post results,
questions and approval requests into a postbox the user can act on. Agent output
can be turned into structured reports, research write-ups and comparisons via
reusable templates. The cockpit owns its own state but connects to existing
systems (wikis, databases, MCP servers, channels) rather than replacing them.

Guiding principle: MCP is the universal seam. Every tool, data source and
channel is registered at runtime through the MCP gateway, never hard-wired —
this is what keeps the system modular and vendor-neutral. Agent capability comes
on two axes: tools and data (what an agent acts on, wired through MCP) and skills
(packaged procedural know-how the agent follows — a SKILL.md, optionally bound to
a fixed command). Both are pluggable, never baked into agent code.

## 2. Usage scenarios & users

Primary users: knowledge workers and teams without deep programming knowledge.
The UI must feel like configuring staff, not writing code — forms and wizards,
sane defaults, plain language, no jargon.

Representative scenarios:
- Research agent: given a goal and source documents, gathers and synthesises
  information and returns a structured research report.
- Monitoring agent (scheduled/event): runs on a cron or reacts to an event
  (new document, webhook), checks something, and posts a notification.
- Comparison / reconciliation: two runs produce structured results; the cockpit
  diffs them on a shared schema and renders a comparison report.
- Approval workflow: an agent proposes an action, pauses, and waits for a human
  to approve / edit / reject in the postbox before continuing.
- Knowledge-grounded agent: reads from a connected wiki, vector DB or graph DB
  to answer with the organisation's own context.

## 3. Functional requirements

Agent lifecycle
- Create, configure, enable/disable and monitor agents.
- Define role, goal, instructions and guardrails (which actions need approval).
- Assign one LLM connection, N tools, N skills, N data sources, a default
  output template.

Tools & data
- Register MCP servers; auto-discover their tools; enable a subset per agent.
- Register data sources: vector, graph, relational, document, wiki.
- Connect any plain REST API by wrapping it as a virtual MCP endpoint.
- One generic "add server/source" form rendered from a config schema — no
  hard-coded UI per integration.

Skills & know-how
- Register skills (open SKILL.md format: name, description, instructions,
  optional bundled scripts/resources); enable a subset per agent.
- Two invocation modes: model-invoked (matched by description, progressive
  disclosure) and fixed command (deterministic, repeatable procedure).
- Author skills in-app (create / validate / test SKILL.md), aided by an
  AI-assisted skill-creator that drafts a skill from a plain-language description.
- Executable skills (bundled scripts) run only in an isolated sandbox (see §9).

LLM
- Register LLM connections (any provider via LiteLLM), with defaults and limits.

Control / triggers
- Four run modes: on demand, scheduled (cron), event-driven, autonomous (loop).
- Pass a goal and optional documents into a run.

Monitoring & postbox
- Live run status and traces; cost and token metrics.
- A postbox where agents post results, questions and approval requests; users
  accept / edit / respond / ignore; responses resume the run.
- Optional routing of postbox items to communication channels (Slack, email...).

Output
- Define output templates for reports, research and comparisons.
- Enforce structured output (typed schema) so data is reliably structured.

Platform
- User management with roles/permissions (OIDC).
- Internationalisation (UI default German, i18n-ready).
- Modular, swappable persistence (single-node default, external DB for clusters).

## 4. Tech stack (all open source)

Backend / control API
- Python 3.12+, FastAPI, Pydantic v2
- SQLAlchemy 2.0 (async) + Alembic; deps via `uv`
- Agent runtime: LangGraph (`interrupt()` for HITL / postbox)
- Durable execution (pluggable): in-process scheduler for dev; Hatchet or
  Temporal for production durability/HA — the runtime must work with or without it
- Event bus: Redis Streams (or NATS)
- LLM gateway: LiteLLM (one endpoint, virtual keys, cost tracking)
- MCP gateway: MCPJungle (default); IBM ContextForge to wrap REST/gRPC as MCP
- Structured output: Instructor + Pydantic; rendering: Jinja2
- Skills: open SKILL.md format (frontmatter name/description + Markdown + optional
  scripts); the cockpit loads and injects them itself, so skills work with any
  LLM. Executable skills run in an isolated sandbox (restricted subprocess /
  container, least-privilege)
- Observability: Langfuse + OpenTelemetry

Persistence (internal system-of-record)
- Default (single node / dev): SQLite + sqlite-vec
- Cluster / HA: PostgreSQL + pgvector
- The switch is connection-string only; no DB-specific code outside repositories

Connected data sources (registered as DataSource records, NOT the app DB)
- Graph: Neo4j / FalkorDB · Relational: external PostgreSQL · Vector: Qdrant
- Human-readable: Wiki.js / Docmost (connected, never rebuilt) — via MCP or a
  thin driver adapter

Frontend
- Angular 21 (LTS — the dev Node v22.14 can't run the Angular 22 CLI, which
  needs >=22.22.3; bump after a Node upgrade): zoneless (no zone.js), signals-first, standalone
  components, new control flow (@if / @for / @switch)
- Angular Material 3 (M3) + Angular CDK; OnPush on every component
- Embeddable widgets via Angular Elements (createCustomElement) → Web Components
- Forms: typed Reactive Forms (Signal Forms is experimental — adopt after v22)
- Tests: Vitest; i18n: @angular/localize or Transloco (default locale `de`)

Auth
- Keycloak (OIDC); the app stores role→permission mappings and ownership only

## 5. Architecture

Three planes, each a separate module with a clean API/MCP boundary:
- Control plane — cockpit UI + control API + domain model (system-of-record)
- Execution plane — LangGraph runtime + durable-execution / trigger layer
- Tool/data plane — MCP gateway + LLM gateway + data stores
Cross-cutting — Auth/RBAC (Keycloak), Observability (Langfuse / OTel)

Each domain area is its own bounded module so files stay small and a coding
agent can work on one area in isolation:
agents · tools · skills · data_sources · llm · mcp · triggers · runtime · inbox ·
templates · channels · auth · settings.

## 6. Repository layout

```
backend/
  app/
    api/            # thin FastAPI routers, one file per domain module
    services/       # business logic, one file per domain module
    repositories/   # persistence access, behind interfaces (SQLite/Postgres)
    models/         # SQLAlchemy ORM models
    schemas/        # Pydantic request/response/domain schemas
    runtime/        # LangGraph graphs + agent execution + skill resolution/sandbox
    triggers/       # scheduler, event handlers, durable-exec adapters
    integrations/   # litellm, mcp_gateway, langfuse clients
    core/           # settings, security, secret_ref, db session
    main.py
  alembic/
  tests/
frontend/
  src/app/
    features/       # one folder per feature (agents, tools, runs, inbox, ...)
    shared/         # dumb UI components, pipes, directives
    elements/       # Angular Elements exposed as Web Components
    core/           # services, guards, interceptors, i18n
infra/
  docker-compose.yml        # SQLite default; `--profile postgres` for cluster
  docker-compose.prod.yml
```

## 7. Domain model

Entities (rough shapes; the coding agent defines concrete schemas + migrations):

Agent — id, name, role, goal, description, icon, instructions, llm_connection_id,
tool_ids[], skill_ids[], data_source_ids[], memory {mode: none|short|long, vector_store_ref},
guardrails {requires_approval_for[]}, default_template_id,
status (draft|active|disabled), audit.

LLMConnection — id, name, provider_model (LiteLLM string, e.g. anthropic/...,
ollama/...), api_base, api_key_ref (SecretRef), params {temperature, max_tokens},
limits {cost, rate}, enabled.

MCPServer — id, name, transport (stdio|streamable-http), url | command+args,
config_schema (the form schema rendered by the add-server UI), credentials_ref,
status (connected|error), discovered_tools[] (cache).

Tool — id, name, description, type (mcp|http|builtin), mcp_server_id, tool_name,
input_schema (JSON Schema), requires_approval, scopes, enabled.

Skill — id, name, description (the match/trigger signal for progressive
disclosure), instructions (SKILL.md body), source (inline|file|git|registry) +
source_ref, resources[] (bundled files/scripts), commands[] (fixed-command
triggers, each with optional input_schema), invocation (model_invoked|command|
both), allowed_tool_ids[] (tools the skill may use, optional), requires_approval,
scopes (sandbox limits for bundled scripts), enabled, audit.

DataSource — id, name, kind (vector|graph|relational|document|wiki),
mcp_server_id | connection_ref (driver + SecretRef), capabilities (read|write|
search), [vector: embedding_model, dimension, collection], enabled.

Trigger — id, agent_id, mode (on_demand|scheduled|event|autonomous),
[scheduled: cron, timezone], [event: source, filter],
[autonomous: loop {interval, stop_condition, budget}], enabled.

Run — id, agent_id, trigger_id, status (queued|running|waiting_human|completed|
failed), input {goal, documents[], params}, thread_id (LangGraph checkpoint),
result (json), rendered_outputs[], metrics {tokens, cost, duration}, trace_id
(Langfuse), started_at, finished_at.

InboxItem — id, run_id, agent_id, type (approval_request|question|notification|
result), payload {action_request {action, args}, description_md},
allowed_responses (accept|edit|respond|ignore), status (pending|answered|
expired), response, responded_by, responded_at, channel_ids[].

Template — id, name, kind (report|research|comparison), output_schema (Pydantic/
JSON Schema), render_template (Jinja2), format (markdown|html|pdf|docx),
[comparison: compare_config {run_a, run_b, fields}].

Channel — id, name, kind (slack|email|matrix|webhook), connection_ref |
mcp_server_id, direction (in|out|both), routing (which InboxItem types), enabled.

Role — id, name, permissions[] (e.g. agent.create, tool.manage, run.approve);
membership resolved via Keycloak claims.

Setting — key, value (json), scope (global|user|agent). Secrets are stored only
as SecretRef pointing to an external backend (env / Vault), never plaintext.

Relationships:
- Agent 1–N Trigger · Agent 1–N Run · Agent N–1 LLMConnection
- Agent N–M Tool · Agent N–M Skill · Agent N–M DataSource · Agent N–1 Template (default)
- Skill N–M Tool (a skill may call tools, optional)
- MCPServer 1–N Tool · MCPServer 1–N DataSource (optional)
- Trigger 1–N Run · Run 1–N InboxItem · Channel N–M InboxItem (routing)

## 8. Core behaviours

- Postbox is a state machine. LangGraph `interrupt()` sets Run.status =
  waiting_human and creates an InboxItem (status = pending). A human response is
  replayed into the checkpoint (Run.thread_id) and the run resumes. This is the
  agent "reply" mechanism.
- Structured-output pipeline. Template.output_schema constrains agent output via
  Instructor → typed JSON in Run.result → Jinja2 renders rendered_outputs. A
  comparison is a structured diff of two Run.result objects on the same schema.
- Generic integration form. The add-server / add-source UI is rendered from
  MCPServer.config_schema; users enter values and secrets — no per-integration UI.
- Skill resolution. At run time the runtime matches the task against enabled
  skills by description and injects matching skill instructions into the agent
  context (progressive disclosure); a fixed command invokes its skill
  deterministically, bypassing model choice. Executable skills run their scripts
  only in the sandbox (§9), approval-gateable via the postbox.

## 9. Hard rules (non-negotiable)

1. File length <= 400 lines, target <= 300. One responsibility per file. Split
   before adding more.
2. Backend layering: routers (thin, I/O only) -> services (logic) -> repositories
   (persistence). Never put DB queries in routers or services.
3. Keep ORM models (models/) and Pydantic schemas (schemas/) separate.
4. Persistence behind repository interfaces. SQLite and Postgres differ only by
   connection string — no engine-specific SQL in services.
5. No secrets in code or DB. Use Pydantic Settings + a SecretRef indirection
   (env / Vault). Store references, never plaintext credentials.
6. Frontend: standalone components, signals for state, OnPush, no zone.js.
   Smart/dumb split: feature components hold state, shared components are pure.
7. Embeddable cockpit pieces are exposed as Web Components via @angular/elements.
8. UX target: users without deep programming knowledge — forms and wizards,
   sane defaults, plain language, no jargon in the UI.
9. i18n: every UI string via an i18n key. Code, identifiers, comments and commit
   messages in English; the UI ships German first.
10. Tests required for every service and component (pytest / Vitest). New module
    => new test file.
11. Executable skills run untrusted code: only in an isolated, least-privilege
    sandbox (restricted subprocess / container), never in the control-plane
    process; no host FS/network beyond declared scopes; execution is
    approval-gateable and audited.

## 10. Adding capabilities — tools & data (MCP-first), skills (SKILL.md)

- Register MCP servers in the gateway. The cockpit reads the server's config
  schema and renders an "Add server" form where secrets go into form fields
  (Smithery-style config JSON as the model). No manual env/args wiring for users.
- Any plain REST API -> wrap as a virtual MCP endpoint via ContextForge. Do not
  bake API calls into agent code.
- Skills are added differently (no MCP server needed): author or import a
  SKILL.md via the in-app skill editor or the AI-assisted skill-creator; a skill
  may declare the tools it uses. Executable skills are sandboxed (§9).

## 11. Commands

- `docker compose up` — full stack (add `--profile postgres` for the cluster DB)
- backend dev: `uv run uvicorn app.main:app --reload`
- migrations: `uv run alembic upgrade head`
- frontend dev: `ng serve` · build Web Components: `ng build`
- tests: `uv run pytest` · `ng test` (Vitest)

## 12. Definition of Done

A change is done when: the file is < 400 lines, layered correctly, covered by a
test, all UI strings are i18n keys, and it runs on both the SQLite default and
the Postgres profile.

## 13. Use our Coding Skill better-coding-workflow

## 14. Code-comments, docs and readme allways english

## 15. Implementation plan & roadmap

The milestone roadmap (M0-M9), build strategy, open decisions and a progress log
live in [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md). This file is
the contract (what to build); that plan is the sequence (how and in what order) —
keep both in sync as milestones land.

#