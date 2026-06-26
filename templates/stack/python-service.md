# Stack — Python Web Service
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/core/config.md, templates/backend/http.md, templates/backend/database.md, templates/backend/observability.md, templates/backend/quality.md, templates/backend/features.md, templates/backend/messaging.md, templates/stack/python-lib.md, templates/base/infra/cicd.md, templates/base/security/devsecops.md, templates/base/data/data-quality.md]

Abstract rules for any Python web service or API. Never used directly —
always extended by a framework-specific stack (Flask, FastAPI, Django).
Covers conventions that are shared regardless of framework choice.

---

## Stack
[ID: python-service-stack]

- Language: Python 3.11+
- Framework: [Flask / FastAPI / Django]
- Package manager: [pip / uv / poetry]
- Linter: ruff
- Formatter: ruff format
- Type checker: mypy (strict mode)
- Test runner: pytest
- ORM: [SQLAlchemy 2.x / Django ORM]
- Migrations: [Alembic / Django Migrate]
- Production server: [gunicorn / uvicorn + gunicorn]
- Distribution: Docker image / [platform]

---

## Runtime version pinning
[ID: python-service-version-pinning]

The Python version is declared in several places that MUST agree, or a
change to one silently diverges and ships an untested runtime:

- the Docker base image (`FROM python:X.Y.Z-...`) — the shipped runtime
- the CI gate's `setup-python` version — the tested runtime
- `mypy`'s `python_version` and `requires-python` — the declared runtime

Rules:

- Pin the Python version identically across all four and bump them in
  lockstep — a base-image major/minor jump is a deliberate, coordinated
  PR, never a dependency-bot auto-merge. A base-image bump alone passes
  CI green (the gate tests its own `setup-python`, not the image's) while
  shipping an untested runtime
- Pin CI's `setup-python` to the exact version the image ships, so every
  gate validates the production runtime, not a trailing patch
- Hold `ruff`'s `target-version` as a style floor — it MAY deliberately
  trail the runtime by one minor to avoid the formatter rewriting code to
  brand-new syntax that is less readable or visually ambiguous

---

## Layered architecture
[ID: python-service-layers]
[EXTEND: backend-quality]

```
HTTP handler / view / route
        ↓
    Service function          ← business logic lives here
        ↓
    Repository / ORM query    ← data access lives here
```

- Repository layer returns domain objects, not ORM model instances
  passed to the caller

---

## Project structure
[ID: python-service-structure]

Overridden by each framework stack. The common principle:

- One directory per feature domain — not one directory per layer
- `services/[feature].py` — business logic, no framework imports
- `tests/component/` — handler-level tests
- `tests/integration/` — tests against real infrastructure

---

## Configuration
[ID: python-service-config]
[EXTEND: base-config]

- Use `pydantic-settings` (`BaseSettings`) for all configuration —
  reads from environment variables automatically
- One `Settings` class per application — instantiated once at startup,
  injected where needed, never imported as a global in service code
- Fail fast: missing required settings raise a `ValidationError` on startup

---

## ORM and migrations
[ID: python-service-orm]
[EXTEND: backend-database]

- SQLAlchemy 2.x for Flask and FastAPI — use `select()` style queries,
  no legacy `Query` API
- Migrations managed by Alembic

---

## Testing
[ID: python-service-testing]
[EXTEND: base-testing]

- pytest for all tests
- Test each endpoint/view for: success (2xx), validation error (400/422),
  auth error (401/403), not found (404)
- No mocking of the database in integration tests — use a real test database
- Component test naming: `test_<route_or_function>_<state>_<expected>`
  e.g. `test_create_user_duplicate_email_returns_409`
- Component tests in `tests/component/`, integration tests in
  `tests/integration/`
- Run before every commit: `pytest && mypy src/ --strict`

---

## Observability
[EXTEND: backend-observability]

- `/health` — liveness check
- `/ready` — readiness check (verifies DB and any required external
  dependencies)

---

## Git conventions
[ID: python-service-git]
[EXTEND: base-git]

- Do not commit `.env`, `__pycache__/`, `.mypy_cache/`
- Migrations are committed — never regenerate a migration already merged