# Stack — Django Web Application
[DEPENDS ON: templates/stack/python-service.md, templates/backend/api.md, templates/backend/auth.md]

Extends the Python library stack with Django-specific rules. Covers apps,
ORM, migrations, REST API (DRF or Django Ninja), authentication, admin,
and deployment.

---

## Stack
[ID: django-stack]
[OVERRIDE: python-service-stack]

- Language: Python 3.11+
- Framework: Django 4.2 LTS / 5.x
- REST layer: [Django REST Framework (DRF) / Django Ninja]
- Package manager: [pip / uv / poetry]
- Linter: ruff
- Formatter: ruff format
- Type checker: mypy (strict mode)
- Test runner: pytest + pytest-django
- WSGI server (production): gunicorn
- Distribution: Docker image / [platform]

---

## Project structure
[ID: django-structure]

```
src/
  [project]/
    __init__.py
    settings/
      base.py          # shared settings
      development.py   # overrides for local dev
      production.py    # overrides for production
      testing.py       # overrides for test runner
    urls.py            # root URL configuration
    wsgi.py
    asgi.py
  [app]/               # one Django app per domain
    __init__.py
    models.py
    views.py           # or viewsets.py for DRF
    serializers.py     # DRF serializers / Ninja schemas
    urls.py
    admin.py
    services.py        # business logic — not in views
    tests/
      test_views.py
      test_services.py
manage.py
pyproject.toml
.env.example
Dockerfile
README.md
CLAUDE.md
```

---

## Settings
[ID: django-settings]

- Split settings into a package: `settings/base.py`, `development.py`,
  `production.py`, `testing.py` — select via `DJANGO_SETTINGS_MODULE`
- Read all environment-specific values from environment variables —
  no hardcoded secrets or hostnames in any settings file
- `DEBUG` MUST be `False` in production — enforced by `production.py`
- `ALLOWED_HOSTS` MUST be explicitly set in production
- Use `django-environ` or `python-decouple` for typed env var parsing

---

## Apps and structure
[ID: django-apps]

- One Django app per bounded domain (e.g. `orders`, `inventory`, `users`)
- Apps are self-contained: models, views, serializers, URLs, admin, and tests
  live inside the app directory
- No cross-app model imports — reference related models via FK, not by
  importing the model class directly across app boundaries
- Business logic belongs in `services.py` — views and viewsets are thin

---

## ORM and migrations
[EXTEND: backend-database]

- Use the Django ORM — no raw SQL strings outside of complex analytics queries
  that cannot be expressed with the ORM; annotate these with a comment
- All schema changes via migrations — commit every migration file
- Never edit a migration that has already been applied in any environment
- Name migrations descriptively: `0003_add_order_status_index.py`
- Add `db_index=True` on all ForeignKey fields used in filtering or ordering
- Use `select_related()` for ForeignKey joins and `prefetch_related()` for
  ManyToMany — avoid N+1 queries

---

## REST API (DRF)
[ID: django-drf]

- One `ViewSet` or `APIView` per resource — thin, delegates to `services.py`
- Serializers validate input and shape output — never return model instances
  directly as API responses
- Use `router.register()` to wire ViewSets — do not hardcode URL patterns
- Pagination: use `PageNumberPagination` or `LimitOffsetPagination` globally;
  never return unbounded lists
- Versioning: URI prefix (`/api/v1/`, `/api/v2/`) — set
  `DEFAULT_VERSIONING_CLASS`

---

## Authentication
[EXTEND: backend-auth]
[OVERRIDE: backend-api-statelessness]

- REST API endpoints (DRF/Ninja) MUST be stateless — use JWT or
  token-based auth; no server-side sessions for API consumers
- Server-rendered views MAY use `django.contrib.auth` session auth —
  this is the standard Django pattern for browser-based admin and
  HTML views; the statelessness rule applies to API endpoints only
- Use `djangorestframework-simplejwt` for JWT-based APIs
- Permission classes on every ViewSet — never rely on `IsAuthenticated` alone
  for sensitive operations; use object-level permissions where needed
- Custom user model from project start — `AUTH_USER_MODEL` must be set before
  the first migration is created; changing it later is very expensive

---

## Admin
[ID: django-admin]

- Register every model that operations staff need to manage
- Use `list_display`, `list_filter`, `search_fields` — raw `ModelAdmin`
  without configuration is not useful
- Never use admin as a user-facing product — it is an internal operations tool
- Restrict admin to staff users: `is_staff=True` required

---

## Testing
[EXTEND: python-service-testing]

- `pytest-django` for all tests — no `unittest.TestCase` unless there is a
  specific reason
- Use `@pytest.mark.django_db` only on tests that need database access —
  keeps the test suite fast
- One `settings` fixture using `testing.py` — never use production settings
  in tests

---

## Git conventions
[EXTEND: base-git]

- Do not commit `.env`, `*.pyc`, `__pycache__/`, `.mypy_cache/`, `db.sqlite3`
- `staticfiles/` is gitignored — collect on deploy, not in the repo

---

## Commands
```
python manage.py runserver          # develop
python manage.py migrate            # apply migrations
python manage.py makemigrations     # generate a migration
python manage.py createsuperuser    # create admin user
pytest                              # run tests
mypy src/ --strict                  # type check
gunicorn [project].wsgi:application # production server
```