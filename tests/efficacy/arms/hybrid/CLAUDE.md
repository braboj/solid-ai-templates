# CLAUDE.md — tariff

## 1. Project

`tariff` is a pricing and invoicing web application for Imbra Ltd. It holds a
product catalog, discount rules of several kinds, tax jurisdictions and
customers, and assembles invoices from them.

- Owner: Imbra Ltd
- Repository URL: not provided in the brief. Set it when the repository is created.
- Runtime: local only. No deployment target and no network access.
- Actors: the administrator working in a browser, and another program.
  The other program imports the pricing engine as a library, without the web
  application present, and consumes invoice exports.
- The web application is one caller of the pricing engine, not its owner.
- The store is a local SQLite file. Nothing reaches the network.
- Interfaces: the library's own API and the invoice exports.
  These are the compatibility surface (see 5.6).
- One administrator signs in. Nobody else has an account.
- Personal data: customers are people. Their name, email and postal address
  are stored and named on invoices. The business is in the EU, so the GDPR
  applies (see 5.1).

## 2. Rules: hybrid model

This file inlines the critical, project-specific rules and points to the
templates for the rest. The templates are vendored under
`docs/solid-ai-templates/`. This is a copy of the upstream repository's
`templates/` directory at a pinned revision, not a submodule. Do not add a
submodule. Refresh the copy by replacing the directory with a newer copy, and
record the revision in the pull request that does it.

Paths below are relative to `docs/solid-ai-templates/`. Read the files
relevant to the task before acting on it.

### 2.1 Every template in this project's chain

- `templates/base/core/agents.md` (format rules for this file)
- `templates/base/core/quality.md`
- `templates/base/core/git.md`
- `templates/base/core/docs.md`
- `templates/base/core/readme.md`
- `templates/base/core/testing.md`
- `templates/base/core/review.md`
- `templates/base/core/oop.md`
- `templates/base/core/config.md`
- `templates/base/core/cli.md`
- `templates/base/core/examples.md`
- `templates/base/language/python.md`
- `templates/base/workflow/quality-gates.md`
- `templates/base/workflow/ai-workflow.md`
- `templates/base/security/security.md`
- `templates/base/security/devsecops.md`
- `templates/base/data/data-modeling.md`
- `templates/base/data/data-quality.md`
- `templates/base/infra/cicd.md`
- `templates/base/infra/containers.md`
- `templates/backend/http.md`
- `templates/backend/database.md`
- `templates/backend/observability.md`
- `templates/backend/quality.md`
- `templates/backend/features.md`
- `templates/backend/messaging.md`
- `templates/backend/templating.md`
- `templates/frontend/ux.md`
- `templates/frontend/quality.md`
- `templates/stack/python-lib.md`
- `templates/stack/python-service.md`
- `templates/stack/python-flask.md`
- `templates/stack/htmx.md`

### 2.2 Adoption boundary

- The chain supplies candidates, not an obligation. This project adopts what
  its needs and material risks warrant, as selected in this file.
- Resolving the chain discovers available rules. It does not authorize work.
- A newer upstream revision or a new candidate rule creates no compliance
  work, ticket or decision record by itself. Nothing MUST be adopted just
  because a template says MUST.
- Declining a candidate needs at most a line in the pull request or
  discussion. It needs no ADR, ticket or decline register.
- Rules adopted here stay in force until this project changes them.
  Upstream MUST text cannot expand the adopted set silently.
- Assess security fixes in tools the project executes promptly. Review new
  conventions only when a project need warrants it.

### 2.3 Precedence

This file governs where it differs from a template. Section 8 lists the
deliberate divergences and declines. Historical records (ADRs, journal) do
not override current rules.

## 3. Stack and commands

- Language: Python 3.12. Framework: Flask 3, server-rendered Jinja, HTMX 2.x
  (Alpine.js only for purely local UI state).
- Store: SQLite file. Access uses SQLAlchemy 2.x `select()` style with
  Alembic migrations, in the `store` package only. Do not use Flask-SQLAlchemy:
  the store must work without Flask.
- Tooling (bindings from `base-python-tooling`):
  - Package manager and runner: `uv`.
  - Lint and format: `ruff`.
  - Types: `mypy` strict.
  - Cognitive complexity: `complexipy`.
  - SAST: `bandit`.
  - Tests and coverage: `pytest` with `pytest-cov`.
  - Hooks: `pre-commit`, including `gitleaks`.
  - All configuration lives in `pyproject.toml`.
- Python version coherence: `requires-python`, mypy `python_version`, the
  interpreter pin (`.python-version`) and any CI `setup-python` all name the
  same version, and change together. Ruff `target-version` MAY trail one minor.

```
uv sync                                        # install from uv.lock
uv run pytest                                  # tests + coverage
uv run ruff check . && uv run ruff format --check .
uv run mypy                                    # strict, from pyproject.toml
uv run complexipy src
uv run bandit -r src
uv run pre-commit run --all-files
uv run flask --app tariff.web:create_app run --host 127.0.0.1
```

- Commit `uv.lock`. Install from it with the locked flag so a stale lock
  fails rather than resolving silently.
- The web server binds to loopback only. Never bind `0.0.0.0` and never set
  `debug` outside a local development session.

## 4. Structure and architecture

`README.md` is the single source of truth for the directory tree. Do not
draw a second tree here. Placement rules:

- The package is `tariff`, under `src/` (source layout). It contains four
  parts: `engine`, `store`, `exports` and `web`.
- `engine` is the pricing engine: catalog items, discount rules, tax
  jurisdictions and invoice assembly, as pure functions and plain data types.
  - No I/O, no clock, no randomness read from globals. Inject them.
  - It MUST NOT import `flask`, `jinja2`, `sqlalchemy`, `tariff.web` or
    `tariff.store`. The library is used with no web application present.
  - Its public API is re-exported from `tariff/engine/__init__.py`. Anything
    not re-exported is private.
- `store` holds SQLite access behind repository interfaces. Repositories
  return domain objects, not ORM rows. `store` and `exports` may import
  `engine`. `engine` never imports them.
- `exports` writes invoice exports and depends only on `engine` types.
- `web` holds the Flask application factory, blueprints, templates and
  static assets. Handlers are thin: decode, call a service or the engine,
  render. Business logic never lives in a handler or template.
  - Full pages go in `templates/`.
  - HTMX fragments go in `templates/partials/`, named for what they render.
  - No cross-blueprint imports.
- Migrations live in `migrations/`. Synthetic test data lives under `tests/`.
- Discount rules of several kinds use the Strategy pattern, one class per
  kind behind one interface. Adding a kind adds a class and a registry
  entry, not a branch in the engine.
- An abstract or overridable operation declares no `*args` or `**kwargs`.
- Money is integer minor units or `Decimal`, never `float`.
  - The rounding mode and the rounding point (per line or per invoice) are
    named constants, documented once.
  - Amounts carry an ISO 4217 currency code.
  - Tax rate tables cite their source and effective date
    (`base-data-quality`).
- Internal code trusts validated data. Validate at the boundary: forms,
  imported files and the library's public entry points.

The layering check below runs from the repository root. Keep `FORBIDDEN`
current with the rules above.

```bash
py - <<'EOF'
import ast, pathlib

FORBIDDEN = (
    ("tariff.engine", "flask"),
    ("tariff.engine", "jinja2"),
    ("tariff.engine", "sqlalchemy"),
    ("tariff.engine", "tariff.web"),
    ("tariff.engine", "tariff.store"),
    ("tariff.engine", "tariff.exports"),
    ("tariff.exports", "flask"),
    ("tariff.exports", "tariff.web"),
    ("tariff.store", "flask"),
    ("tariff.store", "tariff.web"),
)
ROOT = pathlib.Path("src")

files = sorted(ROOT.rglob("*.py"))
print("modules inspected: %d" % len(files))
findings = []
for path in files:
    module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    for name in names:
        for src, dst in FORBIDDEN:
            if module.startswith(src) and (
                name == dst or name.startswith(dst + ".")
            ):
                findings.append("%s imports %s" % (module, name))
print("layering violations: %d" % len(findings))
for finding in findings:
    print("  %s" % finding)
raise SystemExit(1 if findings or not files else 0)
EOF
```

Pass condition: the inspected count is above zero and the violation count
is zero. Zero inspected means the root is wrong, not that the tree is clean.

## 5. Project rules (inlined)

### 5.1 Personal data and the GDPR

Customers are natural persons, so every customer field and every invoice
that names one is personal data.

- Erasure and access are library operations, not web-only features.
  `engine` or `store` exposes `export_customer_data(customer_id)` (a copy in
  a portable, machine-readable format) and `erase_customer(customer_id)`.
  The administrator UI calls them. Both are covered by tests, including a
  test that erasure leaves no name, email or postal address anywhere in the
  store, exports or logs.
- Erasure versus invoice retention: invoices are financial records that may
  have to be kept. Default until the owner decides otherwise: erasure
  replaces the personal fields on the customer and on issued invoices with
  an irreversible pseudonym and keeps amounts, tax lines, dates and invoice
  numbers. The owner MUST confirm the retention period and legal basis. Do
  not change this behaviour without a proposal (see section 7).
- Data minimisation: store only the fields the brief lists (name, email,
  postal address). Do not add fields that hold personal data without
  approval.
- Never log personal data, request bodies from customer forms, or full
  invoice contents (`security-logging`, `backend-observability`). Log
  identifiers only.
- Test fixtures, seeds and screenshots use synthetic people only. Never
  commit a real customer, an SQLite file, a backup or an export produced from
  real data. The `.gitignore` excludes the database file, backups and
  `exports/` output.
- The SQLite file, backups and invoice exports hold personal data. Treat
  them accordingly: never attach them to issues, journals or pull requests.

### 5.2 Security

Applies `templates/base/security/security.md`, selected as follows.

- Authentication (one administrator):
  - Hash the password with Argon2, bcrypt or scrypt.
  - Compare secrets in constant time.
  - Throttle repeated failed sign-ins.
  - Regenerate the session ID on login and invalidate it on logout.
  - The password hash and the Flask `SECRET_KEY` come from the environment,
    never from source and never with a default.
- Sessions use a cookie, so CSRF protection is mandatory. Use the
  framework's CSRF mechanism on every `POST`, `PUT`, `PATCH` and `DELETE`,
  including HTMX requests. Send the token via the `hx-headers` on the body
  element or a hidden field. `GET` never changes state. Set `HttpOnly`,
  `SameSite=Lax` and `Secure` where the deployment allows it.
- Jinja autoescape stays on. Never use `|safe` or `Markup` on data that
  came from a user, a catalog field or an import. Build no HTML by string
  concatenation.
- SQL: parameterised statements through SQLAlchemy only. No f-string SQL.
- Security headers via one `after_request` hook: a strict
  `Content-Security-Policy` with no `unsafe-inline` or `unsafe-eval`,
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy` and `Permissions-Policy`. Serve HTMX and any script from
  local static files, not a CDN. Pin static MIME types in code.
- Errors: never show stack traces, paths or SQL to the browser. Log details
  server-side. Login errors say "invalid credentials".
- No untrusted deserialisation (`pickle`, `yaml.load`, `eval`, `exec`).
  Imports and exports use JSON or CSV, validated against a schema at the
  boundary.
- Nothing reaches the network, so no outbound HTTP client is added. Adding
  one is a new trust boundary and needs approval (`security-ssrf` would then
  apply).
- Secrets, `.env*`, keys and the database file never enter version control.
  `.env.example` carries placeholders only, with names prefixed `TARIFF_`
  (`base-config`). Validate required configuration at start-up and fail
  fast. Agents follow `security-agent-secrets`: never read or print secret
  files or values.
- CI-independent secret scanning: `gitleaks` in pre-commit over full history.
  Dependency vulnerabilities: `pip-audit` against the locked set, run
  locally with the gates. License review before adding a dependency.

### 5.3 Python safety and style

- `mypy` strict passes with zero errors. No `Any` in the public API. Every
  public function and class member is annotated and has a Google-style
  docstring (ruff `D` rules, tests exempt).
- No bare `except:` and no `except Exception:` except at a top-level
  boundary that logs and re-raises or returns an error response. No mutable
  default arguments. No debug `print`, `pdb`, or commented-out code.
- Errors raised on purpose derive from one base, `TariffError`, and each
  also derives from the built-in its site raised before. A test walks every
  `raise` in the package and fails on one outside the hierarchy
  (`base-python-errors`).
- The library attaches only `logging.NullHandler()` to its own logger and
  installs no writing handler. The web tier configures real logging.
- Functions and modules: cognitive complexity within the configured limit,
  nesting depth of at most three levels, no boolean flag parameters, named
  constants instead of magic numbers, no circular imports.
- Identifiers are ASCII. Comments, docstrings and documentation are not
  restricted. Files are UTF-8 with LF line endings. Commit `.editorconfig`
  and `.gitattributes` (`* text=auto`). Any program that writes text sets
  its encoding and newline explicitly.
- Comments explain a non-obvious why, sit directly above the item, and never
  cite a ticket, PR or ADR number.
- Probe or scratch scripts are named `probe_*` and deleted before the commit
  that uses their findings. Anything left in `scripts/` is invoked by a
  documented command or by CI.
- Every wait on a thread, process or connection is bounded and reports why
  it gave up.

### 5.4 Web and HTMX

- Server-rendered HTML is the response format. Detect HTMX with the
  `HX-Request` header, return the partial for HTMX requests, and the full
  page otherwise (pages work without JavaScript).
- Validation errors return `422` and re-render the form partial with inline
  errors and the submitted values. State-changing routes use `POST` or
  another non-`GET` method.
- URIs: lowercase, hyphenated, plural nouns, no trailing slash. Query
  parameters are camelCase. Parse typed query parameters explicitly so
  absent, valid and invalid are three distinct states, and invalid returns
  `400`. Never rely on type-coercing helpers that fall back to a default.
- Every HTMX request shows loading state (`hx-indicator`) and disables the
  triggering element during the request.
- UI accessibility target is WCAG 2.1 AA (`templates/frontend/ux.md`):
  keyboard operable, visible `:focus-visible`, labelled controls and
  landmarks, and no colour-only meaning. Check it manually before shipping a
  new interactive component.

### 5.5 Data and migrations

- Schema changes go through Alembic migrations only. Never edit the SQLite
  file by hand and never edit a merged migration.
- Every migration is reversible and covers one logical change. Migrations
  preserve personal-data handling (5.1), so a migration MUST NOT copy
  personal data into a new column or table without approval.
- Naming, normalisation, types and foreign keys follow
  `templates/base/data/data-modeling.md`. Foreign keys are declared and
  enforced (`PRAGMA foreign_keys=ON` on every connection). Timestamps are
  UTC. Every query has a bound or a filter.
- One transaction per unit of work. Never hold a transaction open across a
  request boundary.
- Tests run against real SQLite files in a temporary directory, never
  against mocks of the store.

### 5.6 Public interfaces

The library API (`tariff.engine` exports) and the invoice export format are
consumed by another program.

- Removing or renaming a public symbol, or changing a field, ordering,
  encoding or rounding in an export, is a breaking change. Deprecate first,
  with a `DeprecationWarning` naming the replacement and removal version.
- Such a change needs an ADR in `docs/decisions/` and a `CHANGELOG.md` entry
  saying what breaks and how to migrate. Version with SemVer.
- Exports include an explicit format version field. At least one test asserts
  the export against a fixed, independently derived vector, not against the
  library's own output (`testing-external-definition`).

### 5.7 Testing

Applies `templates/base/core/testing.md`.

- `pytest`. Tier is derived from the directory: `tests/unit/` (fast
  default), `tests/integration/` (real SQLite, Flask test client) and
  `tests/e2e/` (opt-in, browser against the app served in-process on an
  ephemeral port 0). The default run is unit plus integration.
- Coverage of new code is at least 90%. The overall gate is 80% (new-project
  policy) and does not regress.
- The engine is pure and is tested without mocks. Money, tax and discount
  logic gets parametrised cases and boundary cases (zero, negative, rounding
  half-way, stacking order). Expected values come from independent
  calculation (a statute, a hand-worked invoice), never from running the
  engine and pasting its output. Record the source beside each vector.
- A test asserting "nothing found" also asserts its inputs were reached.
- Each test is independent. Set and clear environment variables per test.
  No test touches the host outside its temporary directory.
- Do not weaken or delete an existing test to turn a run green without
  stating why. A green suite is not evidence of the change until CI or the
  full local gate has run.
- Test naming: `test_<unit>_<state>_<expected>`.

### 5.8 Git

- Never commit to `main`. Branch names: `feat/…`, `fix/…`, `chore/…`,
  `docs/…`.
- Conventional commit prefixes (`feat:`, `fix:`, `chore:`, `docs:`,
  `refactor:`, `style:`, `test:`). Imperative mood, subject under 80
  characters. A single-commit branch that closes an issue carries the issue
  reference in the commit subject.
- Small, focused pull requests, one concern each. Run the local gates before
  committing. Review the diff against the base before merging (priority:
  security, correctness, clarity, conventions).
- Never force-push, including `--force-with-lease`. Merge `main` into a
  behind branch. Repeat the closing keyword before each issue number, and
  never write a closing keyword beside an issue that should stay open.
- Regenerate derived artifacts in the same change that edits their source.
- Never commit build output, virtual environments, `.env*`, keys, database
  files or exports. Commit `uv.lock`. Treat the repository as public.
- Releases are annotated tags `vX.Y.Z` cut from `main`. The release process
  and its pre-release checks are in `templates/base/core/git.md` and are
  referenced from `docs/PLAYBOOK.md`.

### 5.9 Documentation and content rules

- Keep `README.md` (nine sections per `base-readme`), `docs/ONBOARDING.md`
  and `docs/PLAYBOOK.md` (structures in `templates/base/core/docs.md`),
  `docs/dev-journal.md` (required, oldest first) and `CHANGELOG.md`
  (entries of at most 40 words, kept by the change that causes them).
- Update the relevant documents before every commit. The README's structure
  section is the only directory tree.
- Do not state a figure about the tree (a count of files, tests, rules) in
  prose unless a generator produces it.
- Write in present tense, in full sentences. Show commands in fenced blocks.
- Decision records (`docs/decisions/NNN-slug.md`, frontmatter format from
  `base-docs`) are required only for changes a user of the library or the
  export can observe, such as the public API, export format or erasure
  semantics. Prose style, tool choice, layout and refactors end in the pull
  request.
- Never put a real customer's data in any document, journal or issue.

## 6. Workflow

### 6.1 Plan before implementing

For any feature or non-trivial change, write the plan first: files to touch,
signatures or outline, edge cases and the assumptions made explicit. Do not
write implementation code until it is approved. Single-line fixes and
changes already fully specified are exempt. If a constraint invalidates the
plan mid-way, stop and re-surface the options.

### 6.2 Review and audit scopes

- **Code review scope:** read `templates/base/core/review.md`,
  `templates/base/core/quality.md`, `templates/base/language/python.md`,
  `templates/base/security/security.md`, `templates/base/core/testing.md`,
  and section 5 of this file. Apply the priority order security,
  correctness, clarity, conventions. Verify a finding before reporting it, as
  `review.md` describes.
- **Structure audit scope:** run after initial setup, after adding a layer
  and before a release. Verify every MUST in
  `templates/base/core/docs.md`, `templates/base/core/readme.md` and
  `templates/base/core/git.md`, plus `templates/stack/python-flask.md`,
  `templates/stack/python-lib.md`, `templates/stack/htmx.md` and the
  layering check in section 4. Check each sub-clause independently.
- **Quality gates:** `templates/base/workflow/quality-gates.md` defines the
  model. Layer 1 is editor settings mirroring the gates, tracked in
  the repository. Layer 2 is `pre-commit`. Layer 3 is the same commands run
  in CI. No CI platform is specified yet, so until one exists, layer 3 is the
  full local gate list in section 3, run before every merge (see section 8).
- **CI/CD and DevSecOps:** referenced from `templates/base/infra/cicd.md` and
  `templates/base/security/devsecops.md`. Only the build, lint, test and
  scan stages apply here (see section 8).

### 6.3 End-of-session audit

Before ending a session, execute the end-of-session audit defined in
`scope.md`, as `templates/base/core/agents.md` §6.3 directs. Execute each
item of its checklist. Do not summarize it, paraphrase it or reduce it to
bullets. Then update `docs/dev-journal.md` with the session entry (heading
`## YYYY-MM-DD — Short theme`, with Tool, Key changes, PRs merged, Issues
closed/created, and Lesson or decisions).

## 7. Off-limits paths

The following MUST NOT be modified without explicit approval. Before
changing one, propose the change with a rollback strategy and the tests that
would catch a regression. Approval covers that plan only. A diff touching
one of these paths says so at the top of its summary. Prose-only changes
(comments and documentation, with no directive comments) are ordinary work.

- Authentication and session code (`src/tariff/web/auth*` and session or
  secret-key configuration).
- Money-critical engine code: invoice totals, tax calculation and rounding
  (`src/tariff/engine/` modules that compute them). The blast radius is
  every invoice ever issued.
- Personal-data operations: `export_customer_data`, `erase_customer` and
  anything that copies or retains customer fields.
- Database migrations (`migrations/`).
- `.env*` and anything handling secrets, keys or the password hash.
- CI/CD workflow definitions (`.github/workflows/` or the equivalent, once
  one exists), and `.pre-commit-config.yaml` hook definitions.
- `docs/solid-ai-templates/`. It is a vendored copy of the governing rules.
  A one-line change here rebinds every rule in this file, and no linter or
  test reads it. Refresh it only through a proposed change.

These paths match the intended layout. Adjust them to the real files when
those exist, and keep this list and the layering check in section 4 in step.

## 8. Declined candidates and revisit triggers

Declining a candidate needs no ADR (section 2.2). These are recorded because
they are deliberate and each names what reopens it.

| Candidate | Status | Revisit trigger |
| --- | --- | --- |
| Containers, Kubernetes, image scanning (`base-containers`) | Declined: local-only, no deployment target | Revisit trigger: a deployment target or container packaging is chosen |
| Deploy stages, staging, DAST, IaC scanning (`base-cicd`, `base-devsecops`) | Declined: nothing is deployed | Revisit trigger: the application is hosted anywhere beyond the administrator's machine |
| Hosted CI (layer 3) | Deferred: local full gate stands in | Revisit trigger: the repository is hosted with a CI platform. Then wire the section 3 commands as required checks |
| Multi-factor authentication for the administrator | Not adopted: single local user | Revisit trigger: the app becomes reachable off the local machine or gains a second account |
| HTTPS/HSTS, token auth, HATEOAS, JWT (`backend-http`) | Not applicable: loopback, cookie session, HTML responses | Revisit trigger: a JSON API or network listener is added |
| Messaging, feature flags, distributed tracing (`backend-messaging`, `backend-features`, tracing in `backend-observability`) | Declined: single process | Revisit trigger: a second process or a background job appears |
| SEO, structured data, analytics (`frontend-quality`) | Not applicable: not publicly indexed | Revisit trigger: any page becomes public |
| Mutation testing (`quality-gates-mutation`) | Not adopted | Revisit trigger: the engine suite is mature and a money-path regression escapes it |
| SBOM and release attachment | Not adopted: nothing is published | Revisit trigger: the library is distributed to anyone outside Imbra |

<!-- Generated with solid-ai-templates
(github.com/braboj/solid-ai-templates) -->
