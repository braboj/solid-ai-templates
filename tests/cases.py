"""
E2E test case definitions for solid-ai-templates.

Each test entry has these fields:
  id          short ID used on the command line (e.g. STK-01)
  spec        the spec file this test implements
  stack       stack template file fed to the agent
  answers     interview answers the agent receives
  output_file output format template (defaults to templates/base/core/agents.md)
  extra_files additional template files to include in the prompt
  required    strings that MUST appear in the output
  forbidden   strings that MUST NOT appear in the output
  skip        if present, the test is skipped with this message

Maintenance contract:
  When a template is added or moved, update:
  - stack paths in this file (STK_TESTS, DPL_TESTS extra_files)
  - output_file paths if the format template moves
  - run `py tests/run_smoke.py E2E-01` to verify all paths resolve
"""

# -------------------------------------------------------------------------
# Stack tests (STK)
# -------------------------------------------------------------------------

STK_TESTS = [
    {
        "id": "STK-01",
        "spec": "SAIT-E2E-STK-01-001A",
        "stack": "templates/stack/python-fastapi.md",
        "answers": {
            "Project name": "OrderService",
            "Owner": "Platform team",
            "Repo": "github.com/acme/order-service",
            "Deployment": "Docker to Kubernetes (cloud)",
            "Database": "PostgreSQL via SQLAlchemy 2 + Alembic",
            "Auth": "JWT bearer tokens",
            "Feature flags": "no",
            "Messaging": "no",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Git", "Code conventions", "Testing",
            "Python 3.11", "FastAPI", "SQLAlchemy",
            "pytest",
            "async def",
            "pydantic-settings",
            "feat:",
        ],
        # these are raw template placeholders — if any appear, the agent
        # failed to substitute the interview answers into the output
        "forbidden": ["[your project]", "[owner]", "[repo]", "[platform]"],
    },
    {
        "id": "STK-02",
        "spec": "SAIT-E2E-STK-02-001A",
        "stack": "templates/stack/go-echo.md",
        "answers": {
            "Project name": "MetricsHub",
            "Owner": "Infrastructure team",
            "Repo": "github.com/acme/metricshub",
            "Deployment": "Docker to Kubernetes (cloud)",
            "Database": "PostgreSQL via sqlc + pgx",
            "Auth": "JWT bearer tokens",
            "Feature flags": "yes — OpenFeature Go SDK",
            "Messaging": "no",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Git", "Code conventions", "Testing",
            "Go 1.22", "Echo v4", "sqlc", "pgx",
            "cmd/", "internal/",
            "errgroup", "SIGTERM",
            "OpenFeature",
            "go.sum",
            "feat:",
        ],
        "forbidden": [],
    },
    {
        "id": "STK-03",
        "spec": "SAIT-E2E-STK-03-001A",
        "stack": "templates/stack/python-django.md",
        "answers": {
            "Project name": "CatalogService",
            "Framework": "Django 5.x + Django REST Framework",
            "Database": "PostgreSQL via Django ORM",
            "Auth": "JWT via djangorestframework-simplejwt",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Git", "Code conventions", "Testing",
            "Django", "REST framework",
            "select_related", "prefetch_related",
            "migration",
            "simplejwt",
            "pytest-django", "django_db",
            "feat:",
        ],
        "forbidden": [],
    },
    {
        "id": "STK-04",
        "spec": "SAIT-E2E-STK-04-001A",
        "stack": "templates/stack/node-express.md",
        "answers": {
            "Project name": "NotificationService",
            "Language": "TypeScript",
            "Database": "PostgreSQL",
            "Auth": "JWT",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Git", "Code conventions", "Testing",
            "Node", "Express", "TypeScript", "Zod",
            "middleware",
            "supertest",
            "feat:",
        ],
        "forbidden": [],
    },
    {
        "id": "STK-07",
        "spec": "SAIT-E2E-STK-07-001A",
        "stack": "templates/stack/static-site-astro.md",
        "answers": {
            "Project name": "TechBlog",
            "Language": "TypeScript",
            "Content": "Markdown + MDX",
            "Integrations": "React islands for interactive components",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Git", "Code conventions",
            "Astro", "TypeScript", "MDX",
            "src/content",
            "client:",
            "feat:",
        ],
        "forbidden": [],
    },
    {
        "id": "STK-08",
        "spec": "SAIT-E2E-STK-08-001A",
        "stack": "templates/stack/go-grpc.md",
        "answers": {
            "Project name": "PaymentGateway",
            "Language": "Go",
            "Communication": "gRPC (internal service-to-service)",
            "Auth": "mTLS",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Git", "Code conventions", "Testing",
            "Go", "gRPC", "proto",
            "interceptor",
            "status code",
            "feat:",
        ],
        "forbidden": [],
    },
    {
        "id": "STK-10",
        "spec": "SAIT-E2E-STK-10-001A",
        "stack": "templates/stack/go-lib.md",
        "answers": {
            "Project name": "retrykit",
            "Language": "Go",
            "Distribution": "Go module (pkg.go.dev)",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Commands",
            "Git", "Code conventions", "Testing",
            "Go",
            "doc comment",
            "vX.Y.Z",
            "go.sum",
            "feat:",
        ],
        # go-lib is a library, not a deployable service
        "forbidden": ["Dockerfile", "Deployment"],
    },
    {
        "id": "STK-11",
        "spec": "SAIT-E2E-STK-11-001A",
        "stack": "templates/stack/python-flask.md",
        "answers": {
            "Project name": "ReportingAPI",
            "Language": "Python",
            "Database": "PostgreSQL via Flask-SQLAlchemy",
            "Auth": "JWT",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Git", "Code conventions", "Testing",
            "Flask", "Python", "SQLAlchemy",
            "create_app",
            "blueprint",
            "pytest-flask",
            "feat:",
        ],
        "forbidden": [],
    },
    {
        "id": "STK-12",
        "spec": "SAIT-E2E-STK-12-001A",
        "stack": "templates/stack/python-service.md",
        "answers": {
            "Project name": "DataPipelineWorker",
            "Language": "Python",
            "Framework": "none (plain Python service)",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Commands",
            "Git", "Code conventions", "Testing",
            "Python",
            "ruff",
            "pytest",
            "feat:",
        ],
        # python-service is framework-agnostic
        "forbidden": ["FastAPI", "Flask", "Django"],
    },
    {
        "id": "STK-13",
        "spec": "SAIT-E2E-STK-13-001A",
        "stack": "templates/stack/python-grpc.md",
        "answers": {
            "Project name": "MLInferenceService",
            "Language": "Python",
            "Communication": "gRPC (internal service-to-service)",
            "Auth": "mTLS",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Commands",
            "Git", "Code conventions", "Testing",
            "Python", "gRPC", "proto",
            "grpcio",
            "servicer",
            "interceptor",
            "feat:",
        ],
        "forbidden": [],
    },
    {
        "id": "STK-15",
        "spec": "SAIT-E2E-STK-15-001A",
        "canary": True,  # smallest chain (~12K tokens) — default live test
        "stack": "templates/stack/python-lib.md",
        "answers": {
            "Project name": "validify",
            "Language": "Python",
            "Distribution": "PyPI package",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Commands",
            "Git", "Code conventions", "Testing",
            "Python",
            "pyproject.toml",
            "docstring",
            "feat:",
        ],
        # python-lib is a library, not a deployable service
        "forbidden": ["Dockerfile", "Deployment"],
    },
    {
        "id": "STK-16",
        "spec": "SAIT-E2E-STK-16-001A",
        "stack": "templates/stack/go-service.md",
        "answers": {
            "Project name": "HealthCheckService",
            "Language": "Go",
            "HTTP framework": "none (standard library only)",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Git", "Code conventions", "Testing",
            "Go",
            "net/http",
            "graceful shutdown",
            "go.sum",
            "feat:",
        ],
        "forbidden": [],
    },
    {
        "id": "STK-18",
        "spec": "SAIT-E2E-STK-18-001A",
        "stack": "templates/stack/nodejs-lib.md",
        "answers": {
            "Project name": "parsekit",
            "Language": "TypeScript",
            "Distribution": "npm package",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Commands",
            "Git", "Code conventions", "Testing",
            "Node", "TypeScript",
            "exports",
            "vitest",
            "feat:",
        ],
        # node-lib is a library, not a deployable service
        "forbidden": ["Dockerfile", "Deployment"],
    },
    {
        "id": "STK-20",
        "spec": "SAIT-E2E-STK-20-001A",
        "stack": "templates/stack/htmx.md",
        "answers": {
            "Project name": "AdminDashboard",
            "Backend language": "Python (Flask)",
            "Templating engine": "Jinja2",
            "Client-side state": "Alpine.js",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Commands",
            "Git", "Code conventions",
            "HTMX", "Jinja2",
            "hx-",
            "fragment",
            "Alpine",
            "feat:",
        ],
        # HTMX is server-rendered hypermedia — SPA patterns must not appear
        "forbidden": ["JSON API", "SPA routing"],
    },
]

# -------------------------------------------------------------------------
# Format tests (FMT)
# -------------------------------------------------------------------------

FMT_TESTS = [
    {
        "id": "FMT-01",
        "spec": "SAIT-E2E-FMT-01-001A",
        "stack": "templates/stack/python-fastapi.md",
        "output_file": "templates/base/core/agents.md",
        "answers": {
            "Project name": "OrderService",
            "Database": "PostgreSQL via SQLAlchemy 2",
            "Auth": "JWT bearer tokens",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Project structure", "Commands",
            "Code conventions", "Git", "Testing",
            "Python", "FastAPI",
            "feat:",
        ],
        # CLAUDE.md has no Cursor-specific directives
        "forbidden": ["alwaysApply", "applyTo", "globs:"],
    },
    {
        "id": "FMT-02",
        "spec": "SAIT-E2E-FMT-02-001A",
        "stack": "templates/stack/python-fastapi.md",
        "output_file": "templates/base/core/agents.md",
        "answers": {
            "Project name": "OrderService",
            "Database": "PostgreSQL via SQLAlchemy 2",
            "Auth": "JWT bearer tokens",
            "Output format": "AGENTS.md (inline model)",
        },
        "required": [
            "1. Project", "Commands", "Code conventions",
            "Git", "Testing",
            "Python", "FastAPI",
            "feat:",
        ],
        # AGENTS.md has no Cursor-specific directives
        "forbidden": ["alwaysApply", "applyTo", "frontmatter"],
    },
]

# -------------------------------------------------------------------------
# Interview tests (ITV)
# -------------------------------------------------------------------------

ITV_TESTS = [
    {
        "id": "ITV-02",
        "spec": "SAIT-INT-ITV-02-001A",
        "stack": "templates/stack/python-fastapi.md",
        "answers": {
            "Project name": "InventoryService",
            "Owner": "Backend team",
            "Deployment": "Docker",
            "Database": "PostgreSQL via SQLAlchemy 2",
            "Auth": "JWT bearer tokens",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "Git",
            "feat:",
            "1. Project", "Commands", "Code conventions", "Testing",
            "Python", "FastAPI",
        ],
        "forbidden": [],
    },
    {
        "id": "ITV-03",
        "spec": "SAIT-INT-ITV-03-001A",
        "stack": "templates/stack/python-fastapi.md",
        "answers": {
            "Project name": "InventoryService",
            "Owner": "Backend team",
            "Deployment": "Docker",
            "Database": "PostgreSQL via SQLAlchemy 2",
            "Auth": "JWT bearer tokens",
            "Test runner override": "Use unittest instead of pytest for all tests",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "1. Project", "Commands", "Git",
            "Code conventions", "Testing",
            "unittest",
        ],
        "forbidden": [],
    },
]

# -------------------------------------------------------------------------
# Deployment tests (DPL)
# -------------------------------------------------------------------------

DPL_TESTS = [
    {
        "id": "DPL-01",
        "spec": "SAIT-E2E-DPL-01-001A",
        "stack": "templates/stack/node-express.md",
        "extra_files": ["templates/base/infra/deployment.md"],
        "answers": {
            "Project name": "PublicAPIService",
            "Owner": "Platform team",
            "Language": "TypeScript",
            "Deployment target": "cloud",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "Deployment",
            "cloud",
        ],
        # cloud target — private CA and air-gap must not appear
        "forbidden": ["private CA", "air-gap", "offline"],
    },
    {
        "id": "DPL-02",
        "spec": "SAIT-E2E-DPL-02-001A",
        "stack": "templates/stack/go-service.md",
        "extra_files": ["templates/base/infra/deployment.md"],
        "answers": {
            "Project name": "InternalPlatformAPI",
            "Owner": "Platform team",
            "Language": "Go",
            "Deployment target": "hybrid (on-premises + cloud)",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "Deployment",
            "hybrid",
        ],
        "forbidden": [],
    },
    {
        "id": "DPL-03",
        "spec": "SAIT-E2E-DPL-03-001A",
        "stack": "templates/stack/python-fastapi.md",
        "extra_files": ["templates/base/infra/deployment.md"],
        "answers": {
            "Project name": "SecureIngestService",
            "Owner": "Platform team",
            "Language": "Python",
            "Deployment target": "offline (air-gapped, no internet access)",
            "Output format": "CLAUDE.md (inline model)",
        },
        "required": [
            "Deployment",
            "offline",
        ],
        "forbidden": [],
    },
]

# -------------------------------------------------------------------------
# All tests merged
# -------------------------------------------------------------------------

ALL_TESTS = STK_TESTS + FMT_TESTS + ITV_TESTS + DPL_TESTS
CANARY_TESTS = [t for t in ALL_TESTS if t.get("canary")]
