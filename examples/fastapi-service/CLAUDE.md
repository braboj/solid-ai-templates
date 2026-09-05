# TaskFlow API

REST API for managing tasks, projects, and team assignments.

- Owner: Platform team
- Repo: github.com/acme/taskflow-api
- Deployment: Docker image (GHCR) -> Railway (production), Docker
  Compose (local)
- Model: inline

> Generation inputs (per ADR-016 — examples are agent-generated
> outputs of the documented pipeline):
>
> - Stack source: `stack/python-fastapi.md` + `backend/auth.md` +
>   `backend/caching.md`
> - Resolved chain: `generated/stack-fastapi.md` (base + backend +
>   python-fastapi)
> - Output format: `base/core/agents.md` (inline model)
> - Project brief: TaskFlow API — Platform team — Python 3.12 /
>   FastAPI / Pydantic v2 / SQLAlchemy 2 async + Alembic / Redis —
>   uv, ruff, mypy strict, pytest — Docker on Railway

This file is self-contained: all rules are inlined, no external
templates need to be read.

## 1. Project

### 1.1 Overview

- Model: inline
- Language: Python 3.12
- Framework: FastAPI
- Runtime: asyncio (async/await throughout)
- Validation: Pydantic v2
- Package manager: uv
- Linter / formatter: ruff + ruff format
- Type checker: mypy (strict mode)
- Test runner: pytest + httpx (AsyncClient)
- ORM: SQLAlchemy 2.x async + Alembic migrations
- Database: PostgreSQL 16 via `asyncpg`
- Cache: Redis 7 via `redis-py` async client
- ASGI server (production): uvicorn + gunicorn
- Distribution: Docker image pushed to GHCR, deployed on Railway

### 1.2 Project structure

```
src/
  taskflow/
    __init__.py
    main.py              # FastAPI app, lifespan, router includes
    config.py            # Settings via pydantic-settings
    dependencies.py      # Shared Depends() — db session, user, cache
    routers/
      tasks.py           # /tasks endpoints
      projects.py        # /projects endpoints
      users.py           # /users endpoints
      health.py          # /health, /ready
    schemas/
      tasks.py           # TaskCreate, TaskUpdate, TaskResponse
      projects.py
      users.py
    services/
      tasks.py           # business logic — pure async functions
      projects.py
      users.py
    models/              # SQLAlchemy ORM models
      task.py
      project.py
      user.py
    db.py                # async engine, session factory
    cache.py             # Redis client, cache helpers
tests/
  conftest.py            # async client, test DB, fixtures
  unit/
    test_services.py
  integration/
    test_tasks.py
    test_projects.py
    test_auth.py
pyproject.toml
.env.example
Dockerfile
docker-compose.yml
README.md
CLAUDE.md
```

- One directory per feature domain — not one directory per layer
- `services/<feature>.py` holds business logic with no framework imports
- All editable config in `config.py` — never hardcoded in source modules

### 1.3 Commands

```bash
uv run uvicorn taskflow.main:app --reload   # develop — hot reload :8000
uv run alembic upgrade head                 # apply migrations
uv run alembic revision --autogenerate -m "describe change"
uv run pytest                               # run tests
uv run mypy src/ --strict                   # type check
uv run ruff check src/ tests/               # lint
uv run ruff format src/ tests/              # format
uv run gunicorn taskflow.main:app -w 4 \
  -k uvicorn.workers.UvicornWorker          # production server
docker compose up                           # start full stack locally
```

## 2. Code conventions

### 2.1 Git

- Branch: `main` (protected) — never commit directly
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`,
  `docs/<scope>`
- Commits: `<type>(<scope>): <summary>` — types: feat, fix, chore,
  docs, refactor, test; subject under 80 characters, imperative mood
- PRs are small and focused — one concern per PR; require one approval
  and passing CI before merge
- Repeat the closing keyword before each issue number:
  `Closes #a, closes #b` — a bare `#b` stays open
- Never force-push a branch, including with `--force-with-lease`; when
  behind `main`, merge `main` in or use `gh pr update-branch`
- After a PR is merged, delete the branch and pull `main` before new work
- Do not commit `.env`, `*.db`, `__pycache__/`, `.mypy_cache/`, `dist/`
- Alembic migrations are committed — never regenerate a migration
  already merged
- Every repository MUST have a `.gitignore` and a committed lockfile

### 2.2 Python

- Follow PEP 8 (enforced by ruff) — fix the code, never disable a rule
  to work around style
- Follow PEP 257 Google-style docstrings — every public symbol has one
- Follow PEP 484 / PEP 526 type annotations — all public functions and
  class members annotated; run `mypy src/ --strict`
- No bare `Any` — use specific types, `TypeVar`, or `TypeAlias`
- Use `from __future__ import annotations` for forward references
- Keep functions small and single-purpose; cognitive complexity <= 15
- Raise specific exceptions — never bare `except:` or `except Exception:`
- No mutable default arguments
- No debug statements (`print()`, `pdb.set_trace()`) in committed code
- Source files UTF-8, ASCII content only, LF line endings

### 2.3 Application setup

- One `FastAPI` instance in `main.py` — no global state elsewhere
- Use the `lifespan` context manager for startup/shutdown — not
  deprecated event handlers
- Initialise the database engine and Redis client in `lifespan`, not at
  module level
- Set `title`, `version`, and `description` on the app instance
- Register all routers via `app.include_router()` in `main.py`

### 2.4 Configuration

- `pydantic-settings` `BaseSettings` in `config.py` — reads from the
  environment automatically
- One `Settings` class, instantiated once at startup, injected via
  `Depends(get_settings)` — never imported as a global in service code
- `.env.example` committed with placeholders; `.env` in `.gitignore`
- Required vars: `TASKFLOW_DATABASE_URL`, `TASKFLOW_SECRET_KEY`,
  `TASKFLOW_REDIS_URL`, `TASKFLOW_ALLOWED_ORIGINS`
- Prefix every env var with `TASKFLOW_` to avoid collisions
- Fail fast: a missing required setting raises `ValidationError` on
  startup
- The port MUST be configurable via environment variable — never
  hardcoded

### 2.5 Routing and HTTP

- One `APIRouter` per feature domain, with a prefix and tags
- Handlers are thin: decode request -> call service -> encode response;
  no business logic in handlers
- Inject auth, DB session, and current user via `Depends()` using
  `Annotated` syntax — avoid bare `= Depends()` in signatures
- Return type annotations on all route handlers — FastAPI uses them for
  OpenAPI
- Path segments MUST be lowercase plural nouns with hyphens:
  `/tasks`, `/projects/{projectId}/tasks` — no verbs, no trailing slash
- Query parameter names use camelCase; reserve `limit`, `skip`,
  `offset`, `expand`, `sortedBy` for framework use
- No unbounded list endpoints — always paginate with an explicit limit
- JSON is the default format; date/time values use ISO 8601
- All traffic served over HTTPS — plain HTTP is not acceptable

### 2.6 Schemas

- Separate request and response schemas — ORM models are never returned
  directly
- `model_config = ConfigDict(from_attributes=True)` on ORM-backed
  response schemas
- All fields explicitly typed — no bare `Any`
- `Field(...)` for all validation constraints (min/max length, regex,
  ge/le)
- Validators via `@field_validator` — no custom `__init__`
- Responses contain only the fields the caller needs — no padding

### 2.7 Error handling

- Raise `HTTPException` with explicit `status_code` and `detail`
- Map domain exceptions to HTTP errors via custom exception handlers
  registered in `main.py`
- Follow RFC 9457 (`application/problem+json`) for the error body shape;
  use 4xx for client errors, 5xx for server errors — never 200 for an error
- Never return stack traces, internal paths, or implementation details
  to the client
- Log every error once with the request ID for traceability

### 2.8 Authentication and authorization

- JWT bearer tokens — issued at `/users/login`, validated via
  `Depends(get_current_user)`
- Validate every JWT: signature, `exp`, `iss`, `aud` — reject tokens
  missing any required claim
- Token lifetime: access <= 15 min, refresh <= 7 days (rotated on use)
- Access tokens MUST arrive in `Authorization: Bearer <token>` only —
  never in cookies or query parameters
- Refresh tokens stored server-side (Redis) so they can be revoked, and
  in `httpOnly`, `Secure`, `SameSite=Strict` cookies on the client
- Fail closed: deny by default, grant explicitly
- Authorise at the service layer, not only in route handlers — a route
  that passes auth may call a service that touches another user's data
- Never trust client-supplied IDs for ownership checks — verify the
  authenticated user owns the requested resource
- Never log tokens, passwords, or secrets — even at DEBUG level

### 2.9 Caching

- Cache-aside (lazy loading) pattern for read-heavy endpoints (project
  lists, user profiles)
- Cache keys namespaced: `taskflow:<entity>:<id>` — e.g.
  `taskflow:projects:42` — never bare IDs, never from unvalidated input
- Every entry has a TTL: 5 min for list responses, 15 min for single
  resources
- Invalidate on write — `DEL` affected keys after a successful mutation;
  prefer targeted deletes over `FLUSHDB`
- Never cache secrets, tokens, PII, or real-time data; never cache
  user-specific data without scoping the key
- Cache failures MUST NOT crash the app — on miss or error, fall through
  to PostgreSQL

### 2.10 Database

- SQLAlchemy 2.x with async engine (`create_async_engine`) and `asyncpg`
- Session injected per request via `Depends(get_db)` — never a global
  session; use the connection pool, never a connection per request
- `select()` style queries only — no legacy `Query` API; avoid
  `SELECT *`
- No N+1 queries — use `selectinload` or `joinedload` for related data
- Add an index for every foreign key explicitly in migrations
- Wrap multi-step writes in a transaction; keep transactions short and
  never hold one across an HTTP request boundary
- All schema changes via Alembic — one migration per logical change,
  each reversible with a `down`

### 2.11 Async conventions

- All route handlers and service functions are `async def`
- Blocking I/O runs in `asyncio.to_thread()` — never block the event loop
- Use `asyncio.gather()` for concurrent independent awaits — never
  `await` inside a list comprehension or a sequential loop
- Use structured concurrency (`asyncio.TaskGroup`) over fire-and-forget;
  background tasks started in `lifespan` get a clean shutdown path
- Pass request context (request ID, user identity) explicitly — never
  via thread-locals

## 3. Quality

### 3.1 Testing

- `httpx.AsyncClient` with `ASGITransport` for all route tests — no sync
  `TestClient`
- One async `client` fixture in `conftest.py`; override dependencies via
  `app.dependency_overrides`
- Test DB is a real PostgreSQL schema, truncated between runs — no
  database mocking, no SQLite substitution
- Test each endpoint for: success (2xx), validation error (422), auth
  error (401/403), not found (404)
- Test naming: `test_<route_or_function>_<state>_<expected>` —
  e.g. `test_create_task_missing_title_returns_422`
- Unit tests in `tests/unit/`, integration tests in `tests/integration/`
- New code MUST reach 90% coverage; total coverage MUST NOT regress and
  SHOULD stay at or above 80%
- Run before every commit: `pytest && mypy src/ --strict`

### 3.2 Observability

- Structured JSON logs (`structlog`) with the request ID injected per
  request; default level INFO — DEBUG/TRACE off in production
- Log errors once, at the top of the call stack; 4xx at INFO, 5xx at
  ERROR
- Never log passwords, tokens, API keys, or PII
- `/health` — shallow liveness check, returns 200 if the process is
  alive; requires no authentication
- `/ready` — deep readiness check, verifies PostgreSQL and Redis
  connectivity, returns 503 when a critical dependency is down
- Assign a trace ID at the service boundary, propagate it via the W3C
  `traceparent` header, and return it on errors (`X-Trace-Id`)
- Instrument with OpenTelemetry; expose Prometheus metrics at `/metrics`
  (request count, latency, error rate); span names use route templates,
  not URLs with IDs

## 4. Identity

Not applicable — TaskFlow API is a backend service with no design system
or brand voice. Its public contract is the OpenAPI schema served at
`/docs` (disabled in production via `openapi_url=None`).

## 5. Review process

### 5.1 Code review

Before merging, review the diff against the base branch in priority order
(highest first):

1. Security — auth enforced at the service layer, no secrets or PII in
   logs, HTTPS-only, no client-trusted ownership checks
2. Correctness — routes thin, services pure-async, no N+1 queries,
   transactions scoped correctly, cache invalidation on write
3. Clarity — names are self-documenting, functions single-purpose,
   cognitive complexity <= 15
4. Conventions — PEP 8 / mypy strict clean, schema separation, RFC 9457
   error shape, URI and query-parameter casing rules

Confirm CI is green. Only merge after the review passes.

### 5.2 Structure audit

- Run `pytest && mypy src/ --strict` before every PR
- Verify `.env.example` lists every required variable and `README.md`
  documents the env reference and commands
- Verify every route has `summary`, `tags`, and an explicit
  `response_model`, and that new endpoints have success / 422 / auth /
  404 tests
- Run the audit after: new project, migration, a new feature domain, or
  before a release

## 6. Session protocol

### 6.1 Start of session

1. Read this `CLAUDE.md` and `README.md` in full before the first change
2. Check the current branch — if not `main`, ask why before proceeding
3. Check `git status` — if uncommitted changes exist, ship the previous
   session's wrap (branch, commit, push, merge) before any new work
4. Clean up stale branches: `git fetch --prune`, then delete local
   branches whose PRs have merged
5. Check the latest CI/CD deploy on `main` completed successfully — flag
   if stuck, failed, or pending
6. Confirm the scope with the user before making changes
7. If the task is ambiguous, ask: "What is the specific deliverable for
   this session?"
8. Review open issues related to the agreed scope before writing code

### 6.2 During the session

- Flag explicitly when a task grows beyond the agreed scope — do not
  silently absorb new requests
- Finishing and committing the current work takes priority over starting
  something new
- Run `pytest && mypy src/ --strict` after every change — do not
  accumulate unverified changes
- When a tool (formatter, codemod, migration autogenerate) touches
  unrelated files, revert the drift before committing and file it
  separately

### 6.3 End of session

When the user signals end of session ("wrap up", "let's finish", "end
session", "close out", or similar), print the full checklist below and
execute each item sequentially. Mark each item done (with result) before
moving to the next. Do not batch, skip, or summarize — visible
sequential execution prevents missed steps.

1. Commits and push — all changes committed and pushed (via PR if
   branch-protected)
2. Close issues — close completed issues (verify auto-close worked)
3. Epic checklists — update epic checklists if relevant
4. Dev journal — add a session entry to `docs/dev-journal.md` (date,
   tool, key changes, PRs merged, issues closed/created)
5. ADRs — A consequential, durable architectural choice with meaningful alternatives
     MUST have an Architecture Decision Record (ADR) in `docs/decisions/` when
     future maintainers need its tradeoffs to safely reconsider it. Examples:
     ownership boundaries, compatibility contracts, or a major dependency strategy.
   Routine naming, formatting, directory creation, document moves, check-output
     refinements, and compliance repairs belong in the issue/PR and current docs.
     They need no ADR unless their consequences meet the threshold above; no
     separate justification for not writing an ADR is required.
6. Migrations — confirm every schema change has a reversible Alembic
   migration committed and applied (`alembic upgrade head`)
7. CLAUDE.md — for each new convention, decide whether it belongs here
   (a rule the agent MUST apply every turn) or in another doc; keep each
   rule to one line
8. README.md — for each new command, dependency, or env var, confirm it
   is reflected; name the section
9. docs/ONBOARDING.md — for each new tool, prerequisite, or setup step,
   confirm it is documented; name the section
10. docs/PLAYBOOK.md — for each new command, script, or workflow,
    confirm it is documented; name the section
11. Tests and types — run `pytest && mypy src/ --strict` and confirm
    both pass
12. Flag gaps — if any item cannot be completed this session, report it
    as pending (never as done) before closing
13. Summary — summarize what was done and what is next
