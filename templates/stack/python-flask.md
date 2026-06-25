# Stack — Flask Web Application
[DEPENDS ON: templates/stack/python-service.md]

Extends the Python library stack with Flask-specific rules for web
applications and APIs. Covers application factory, blueprints, config,
extensions, and deployment.

---

## Stack
[OVERRIDE: python-lib-stack]

- Language: Python 3.11+
- Framework: Flask
- Package manager: [pip / uv / poetry]
- Linter: ruff
- Formatter: ruff format
- Type checker: mypy (strict mode)
- Test runner: pytest + pytest-flask
- WSGI server (production): gunicorn
- Distribution: Docker image / [platform]

---

## Project structure
[OVERRIDE: python-lib-structure]

```
src/
  [app_name]/
    __init__.py          # application factory (create_app)
    config.py            # Config classes (Dev, Test, Prod)
    extensions.py        # extension instances (db, login_manager, etc.)
    blueprints/
      [feature]/
        __init__.py
        routes.py
        models.py
        schemas.py
    templates/           # Jinja2 templates (if serving HTML)
    static/              # static assets (if serving directly)
tests/
  conftest.py            # app fixture, test client
  test_[feature].py
pyproject.toml
.env.example             # committed — never .env
Dockerfile
README.md
CLAUDE.md
```

---

## Application factory
[ID: flask-factory]

- Always use the application factory pattern (`create_app(config=None)`)
- Never use the global `app` object outside of `create_app`
- Register all blueprints and extensions inside `create_app`
- Extensions instantiated in `extensions.py`, initialised with `ext.init_app(app)`

---

## Configuration
[EXTEND: python-service-config]

- Three config classes: `DevelopmentConfig`, `TestingConfig`, `ProductionConfig`
- `FLASK_ENV` / `FLASK_DEBUG` must be `False` in production

---

## Blueprints
[ID: flask-blueprints]

- One blueprint per feature domain (e.g. `auth`, `api`, `admin`)
- Blueprint registered with a URL prefix (`/api/v1`, `/auth`, etc.)
- No cross-blueprint imports — shared logic goes in a service module
- Routes thin — business logic delegated to service functions, not in route handlers
- For multiple API versions that share one contract (same params,
  validation, and response — differing only in implementation), use a
  version registry (`{"v1": ImplV1, "v2": ImplV2}`) plus a blueprint
  factory (`make_api_blueprint(version, impl)` mounted at
  `url_prefix=f"/api/{version}"`). Adding a version is then a one-line
  registry edit with no per-version route duplication. Reserve a
  dedicated per-version module for when a version's contract actually
  diverges — let the divergence earn the split rather than starting there

---

## Request / response
[EXTEND: backend-http]

- Use `abort()` with HTTP status codes rather than raising raw exceptions

---

## Database (if applicable)
[EXTEND: backend-database]

- Use Flask-SQLAlchemy or SQLAlchemy Core — no raw SQL strings
- Migrations managed by Flask-Migrate (Alembic)

---

## Testing
[EXTEND: python-service-testing]

- `pytest-flask` for the test client and app fixture
- One `app` fixture in `conftest.py` — uses `TestingConfig`

---

## Feature flags (if applicable)
[EXTEND: backend-features]

- Inject the flag client via Flask's application context (`g` or a custom
  extension) — avoid module-level globals
- Evaluate flags in the route handler or service function entry point

---

## Messaging (if applicable)
[EXTEND: backend-messaging]

- Use Celery with a Redis or RabbitMQ broker for background task queues —
  Celery workers run as separate processes from the Flask WSGI server
- For SQS or event-streaming use cases, use `boto3` in a dedicated consumer
  script, not inside a Flask request handler
- Define Celery tasks in a `tasks.py` module per app — keep task functions
  thin and delegate to service functions

---

## Git conventions
[EXTEND: base-git]

- Do not commit `.env`, `instance/`, `*.db`, `__pycache__/`, `.mypy_cache/`
- Migrations are committed — never regenerate a migration that is already merged

---

## Commands
```
flask run                  # develop — hot reload
flask db upgrade           # apply migrations
flask db migrate -m "..."  # generate a migration
pytest                     # run tests
gunicorn "app:create_app()" # production server
```