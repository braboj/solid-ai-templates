# InventoryAPI

REST API for warehouse inventory management — stock levels, locations,
suppliers, and purchase orders.

- Owner: Warehouse platform team
- Repo: github.com/acme/inventory-api
- Deployment: Docker image -> Fly.io (production), Docker Compose (local)
- Model: inline

> Generation inputs (per ADR-016 — examples are agent-generated
> outputs of the documented pipeline):
>
> - Stack source: `stack/python-flask.md` + `backend/auth.md` +
>   `backend/jobs.md`
> - Resolved chain: `generated/stack-flask.md` (base + backend +
>   python-flask). The auth and jobs addons are register-only in the
>   chain, so their rules are inlined here directly from
>   `templates/backend/auth.md` and `templates/backend/jobs.md`,
>   specialized to InventoryAPI.
> - Output format: `base/core/agents.md` (inline model)
> - Project brief: InventoryAPI — Warehouse platform team — Python 3.12
>   / Flask 3.x / SQLAlchemy 2 + Flask-Migrate (Alembic) / PostgreSQL /
>   Celery + Redis — uv, ruff, mypy strict, pytest — Docker on Fly.io

This file is self-contained: all rules are inlined, no external
templates need to be read.

## 1. Project

### 1.1 Overview

- Model: inline
- Language: Python 3.12
- Framework: Flask 3.x
- Package manager: uv
- Linter / formatter: ruff + ruff format
- Type checker: mypy (strict mode)
- Test runner: pytest + pytest-flask
- ORM: SQLAlchemy 2.x + Flask-Migrate (Alembic) migrations
- Database: PostgreSQL 16
- Task queue: Celery 5 with a Redis broker
- WSGI server (production): gunicorn
- Distribution: Docker image, deployed on Fly.io

### 1.2 Project structure

```
src/
  inventory/
    __init__.py          # create_app factory
    config.py            # DevelopmentConfig, TestingConfig, ProductionConfig
    extensions.py        # db, migrate, celery instances
    blueprints/
      stock/
        __init__.py
        routes.py        # /api/v1/stock
        models.py        # StockItem, Location
        schemas.py       # marshmallow / dataclass schemas
        services.py      # business logic
      suppliers/
        routes.py        # /api/v1/suppliers
        models.py
        schemas.py
        services.py
      orders/
        routes.py        # /api/v1/orders
        models.py
        schemas.py
        services.py
        tasks.py         # Celery tasks (PO processing, notifications)
    auth/
      routes.py          # /auth/token
      middleware.py      # JWT verification decorator
tests/
  conftest.py            # app fixture (TestingConfig), test client, test DB
  component/
    test_stock.py
    test_suppliers.py
    test_orders.py
  integration/
    test_order_workflow.py
pyproject.toml
.env.example             # committed — never .env
Dockerfile
docker-compose.yml
README.md
CLAUDE.md
```

### 1.3 Commands

```bash
flask run                           # develop — hot reload
flask db upgrade                    # apply migrations
flask db migrate -m "description"   # generate a migration
celery -A inventory.celery worker   # start a Celery worker (local)
pytest                              # run tests
mypy src/ --strict                  # type check
gunicorn "inventory:create_app()"   # production server
docker compose up                   # full local stack (Flask + Postgres + Redis)
```

## 2. Code conventions

### 2.1 Git

- Branch: `main` is protected — never commit directly; feature branches
  as `feat/<scope>`, fixes as `fix/<scope>`, also `chore/`, `docs/`
- Commits: `<type>(<scope>): <summary>` — types: feat, fix, chore, docs,
  refactor, test; imperative mood, subject under 80 characters
- PRs are small and focused — one concern per PR; require one approval
  and green CI before merge
- Repeat the closing keyword per issue: `Closes #a, closes #b` — a bare
  `#b` does not close
- Never force-push, including `--force-with-lease`; when a branch is
  behind, merge `main` in or use `gh pr update-branch`
- After merge, delete the remote and local branch, then pull `main`
- Do not commit `.env`, `instance/`, `*.db`, `__pycache__/`,
  `.mypy_cache/`
- Migrations are committed — never regenerate a migration already merged

### 2.2 Python

- Target Python 3.12; type hints on every function signature, `mypy
  --strict` clean with no `# type: ignore` without a reason comment
- Format and lint with ruff + ruff format — generated and hand-written
  code MUST pass natively, never rely on `--fix` as a post-step
- Names are the primary documentation: verbs for functions, nouns for
  classes, `is`/`has`/`can` for booleans; no single-letter names except
  loop counters and `e` in `except`
- Cognitive complexity <= 15 per function; max nesting depth three —
  use early returns and guard clauses over `else` branches
- No boolean flag parameters — use an enum or two named functions
- Magic numbers and strings MUST be named constants
- No debug statements (`print`, `pdb.set_trace`), no commented-out code,
  no dead code paths in committed code
- Source files are UTF-8, ASCII-only content, LF line endings

### 2.3 Application factory

- `create_app(config=None)` lives in `inventory/__init__.py`
- Register all blueprints and extensions inside `create_app`
- Extensions instantiated in `extensions.py`, initialised with
  `ext.init_app(app)`
- Never use a global `app` object outside `create_app`

### 2.4 Configuration

- Three config classes in `config.py`: `DevelopmentConfig`,
  `TestingConfig`, `ProductionConfig`
- All env-specific values come from environment variables — no hardcoded
  secrets, no real values as defaults
- `FLASK_DEBUG` / `DEBUG` MUST be `False` in `ProductionConfig`
- Required vars: `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`,
  `CELERY_BROKER_URL` — all documented in `.env.example`

### 2.5 Blueprints

- One blueprint per domain (`stock`, `suppliers`, `orders`, `auth`)
- Each registered with a URL prefix: `/api/v1/stock`,
  `/api/v1/suppliers`, `/api/v1/orders`, `/auth`
- No cross-blueprint imports — shared logic goes in a service module
- Routes are thin: decode and validate input, call a service, encode the
  response; no business logic in handlers
- Use `abort()` with explicit HTTP status codes rather than raising raw
  exceptions
- Path segments lowercase with hyphens, plural collection nouns, no
  trailing slash; query-parameter names camelCase, used only for
  filtering, sorting, and pagination

### 2.6 Authentication

- JWT bearer tokens — issued at `/auth/token`, verified via a decorator
  in `auth/middleware.py`
- Validate every JWT: signature, `exp`, `iss`, `aud` — reject a token
  missing any required claim
- Token lifetime: access <= 15 min, refresh <= 7 days (rotated on use)
- Access tokens MUST arrive in `Authorization: Bearer <token>` only —
  never in query parameters
- Refresh tokens stored server-side (Redis) so they can be revoked, and
  in `httpOnly`, `Secure`, `SameSite=Strict` cookies on the client
- HTTPS required for every authenticated endpoint — no exceptions
- Fail closed: deny by default, grant explicitly
- Roles stored in JWT claims; authorise at the service layer, not only
  in route handlers — a route that passes auth may call a service that
  touches another user's data
- Never trust client-supplied IDs for ownership checks — verify the
  authenticated user owns the requested resource
- Log auth failures at WARN with IP, user agent, and username; never log
  tokens, passwords, or secrets even at DEBUG

### 2.7 Database

- SQLAlchemy 2.x ORM — no raw SQL strings; `select()` style queries
  only, no legacy `Query` API, avoid `SELECT *`
- Migrations via Flask-Migrate (Alembic) — one migration per logical
  change, each reversible with a `down`
- No N+1 queries — use `selectinload` or `joinedload` for relations
- Add an index for every foreign key explicitly in migrations
- Wrap multi-step writes in a transaction; keep transactions short and
  never hold one across an HTTP request boundary
- Use the connection pool with explicit limits — never a connection per
  request, never a global session handle

### 2.8 Background tasks

- Celery tasks defined in `tasks.py` per blueprint — handlers are thin,
  delegating to the same service functions the HTTP layer uses; no
  parallel logic paths and no direct DB access in a handler
- Every task MUST be idempotent — safe to re-run; use a dedup key
  (`job_id`, `event_id`) and design for at-least-once delivery
- Retry with exponential backoff and jitter; cap retries at 3, then
  route to a dead-letter queue — never silently drop a failed job
- Log task start and completion at INFO and failures at ERROR with the
  task ID, attempt number, and correlation ID
- Scheduled jobs are defined in code (schedule-as-code), run as a single
  instance via a distributed lock, with documented frequency and latency
- Track task duration, queue depth, and DLQ depth as metrics; alert when
  queue or DLQ depth indicates worker starvation

## 3. Quality

### 3.1 Testing

- `pytest-flask` for the test client and app fixture
- One `app` fixture in `conftest.py` — uses `TestingConfig` and a real
  PostgreSQL test database, reset (truncated) between runs
- No database mocking and no SQLite substitution — integration tests run
  against real PostgreSQL
- Test each route for: success (2xx), validation error (400), auth error
  (401/403), not found (404)
- Celery tasks tested with `task.apply()` (synchronous, no broker for
  unit tests); test the service the task delegates to, plus the retry and
  DLQ paths
- Component test naming: `test_<route_or_function>_<state>_<expected>` —
  e.g. `test_create_stock_item_missing_sku_returns_400`
- Unit/component tests in `tests/component/`, cross-component flows in
  `tests/integration/`
- New code MUST reach 90% coverage; total coverage MUST NOT regress and
  SHOULD stay at or above 80%
- Run before every commit: `pytest && mypy src/ --strict`

### 3.2 Observability

- Structured JSON logs via `structlog` with a request ID injected per
  request; default level INFO — DEBUG/TRACE off in production
- Log errors once, at the top of the call stack; 4xx at INFO, 5xx at
  ERROR; never log passwords, tokens, API keys, or PII
- `/health` — shallow liveness check, returns 200 if the process is
  alive; requires no authentication
- `/ready` — deep readiness check, verifies PostgreSQL and Redis
  connectivity, returns 503 when a critical dependency is down
- Assign a trace ID at the service boundary, propagate it via the W3C
  `traceparent` header, return it on errors (`X-Trace-Id`)
- Instrument with OpenTelemetry; span names use route templates, not
  URLs with IDs; Celery queue and DLQ depth tracked via Flower or custom
  metrics

## 4. Identity

Not applicable — this project has no design system or brand voice.

## 5. Review process

### 5.1 Code review

Before merging, review the diff against the base branch in priority order
(highest first):

1. Security — auth enforced at the service layer, JWT fully validated, no
   secrets or PII in logs, HTTPS-only, no client-trusted ownership checks
2. Correctness — routes thin, services own business logic, no N+1
   queries, transactions scoped correctly, every Celery task idempotent
3. Clarity — names are self-documenting, functions single-purpose,
   cognitive complexity <= 15
4. Conventions — ruff and mypy strict clean, blueprint and schema
   separation, RFC 9457 error shape, URI and query-parameter casing rules

Confirm CI is green. Only merge after the review passes.

### 5.2 Structure audit

- Run `pytest && mypy src/ --strict` before every PR
- Verify `.env.example` lists every required variable and `README.md`
  documents the env reference and commands
- Verify each new route has success / 400 / auth / 404 tests and each new
  Celery task has retry and DLQ tests
- Verify every schema change ships a reversible Alembic migration
- Run the audit after: new project, migration, a new blueprint domain, or
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
5. ADRs — record any architectural decisions in `docs/decisions/`; a new
   directory or content move between documents each needs an ADR
6. Migrations — confirm every schema change has a reversible Alembic
   migration committed and applied (`flask db upgrade`)
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
