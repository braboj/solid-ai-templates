# Stack — FastAPI Application
[DEPENDS ON: templates/stack/python-service.md, templates/backend/concurrency.md]

Extends the Python library stack with FastAPI-specific rules. Covers async
request handling, Pydantic schemas, dependency injection, OpenAPI, and
deployment.

---

## Stack
[OVERRIDE: python-service-stack]

- Language: Python 3.11+
- Framework: FastAPI
- Runtime: asyncio (async/await throughout)
- Validation: Pydantic v2
- Package manager: [pip / uv / poetry]
- Linter: ruff
- Formatter: ruff format
- Type checker: mypy (strict mode)
- Test runner: pytest + httpx (AsyncClient)
- ASGI server (production): uvicorn + gunicorn
- Distribution: Docker image / [platform]

---

## Project structure
[OVERRIDE: python-lib-structure]

```
src/
  [app_name]/
    __init__.py
    main.py              # FastAPI app instance, lifespan, router includes
    config.py            # Settings via pydantic-settings
    dependencies.py      # Shared FastAPI dependencies
    routers/
      [feature].py       # APIRouter per feature domain
    schemas/
      [feature].py       # Pydantic request/response models
    services/
      [feature].py       # Business logic (pure, async)
    models/              # ORM models (if using SQLAlchemy)
    db.py                # Database session / engine setup
tests/
  conftest.py            # async client fixture
  test_[feature].py
pyproject.toml
.env.example
Dockerfile
README.md
CLAUDE.md
```

---

## Application setup
[ID: fastapi-app]

- One `FastAPI` instance in `main.py` — no global state elsewhere
- Use `lifespan` context manager for startup/shutdown (not deprecated events)
- Include all routers via `app.include_router()` in `main.py`
- Set `title`, `version`, and `description` on the app instance

---

## Configuration
[EXTEND: python-service-config]

---

## Routing and dependencies
[ID: fastapi-routing]

- One `APIRouter` per feature domain with a prefix and tags
- Routes thin — delegate business logic to service functions
- Shared logic (auth, DB session, current user) via `Depends()`
- Use `Annotated` for dependency injection — avoid bare `= Depends()` in
  signatures
- Return type annotations on all route functions (FastAPI uses these for
  OpenAPI)

---

## Schemas
[ID: fastapi-schemas]

- Separate request and response schemas — never reuse ORM models as responses
- Use `model_config = ConfigDict(from_attributes=True)` for ORM-backed responses
- All fields explicitly typed — no bare `Any`
- Use `Field(...)` for validation constraints (min/max length, regex, ge/le)
- Validators via `@field_validator` — no custom `__init__`

---

## Async conventions
[EXTEND: backend-concurrency]

- All route handlers and service functions `async def`
- Blocking I/O (file reads, sync DB calls) must run in `asyncio.to_thread()`
- Never `await` inside a list comprehension — use `asyncio.gather()` for
  concurrency
- Use `asyncpg` or `aiosqlite` for async database drivers

---

## Error handling
[EXTEND: backend-http]

- Raise `HTTPException` with explicit `status_code` and `detail`
- Register custom exception handlers in `main.py` for domain exceptions

---

## Database (if applicable)
[EXTEND: backend-database]

- SQLAlchemy 2.x with async engine (`create_async_engine`)
- Session injected per request via `Depends(get_db)` — never a global session
- Migrations managed by Alembic
- Use `select()` style queries — no legacy `Query` API

---

## Testing
[EXTEND: python-service-testing]

- `httpx.AsyncClient` with `ASGITransport` for route tests — no `TestClient`
  (sync)
- One async `client` fixture in `conftest.py`
- Override dependencies with `app.dependency_overrides` in tests

---

## OpenAPI
[ID: fastapi-openapi]

- All routes have `summary`, `tags`, and explicit `response_model`
- Disable OpenAPI in production if the API is not public: `openapi_url=None`
- Keep schema clean — avoid `include_in_schema=False` as a crutch

---

## Feature flags (if applicable)
[EXTEND: backend-features]

- Inject the flag client as a FastAPI dependency via `Depends()` — never
  import it as a module-level global
- Evaluate flags in the route handler or service entry point —
  not deep inside domain logic
- Use `asyncio.to_thread()` if the flag SDK evaluation is synchronous

---

## Messaging (if applicable)
[EXTEND: backend-messaging]

- Use `aio-pika` for RabbitMQ, `aiokafka` for Kafka, or `aiobotocore` for SQS —
  all broker clients must be async
- Initialise the broker connection in the `lifespan` context manager —
  not at module level
- Consumer coroutines run as background tasks started in `lifespan` —
  use `asyncio.create_task()` with structured shutdown

---

## Git conventions
[EXTEND: base-git]

- Do not commit `.env`, `*.db`, `__pycache__/`, `.mypy_cache/`

---

## Commands
```
uvicorn app.main:app --reload      # develop — hot reload at localhost:8000
alembic upgrade head               # apply migrations
alembic revision --autogenerate -m "..."  # generate a migration
pytest                             # run tests
mypy src/ --strict                 # type check
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker  # production
```