# CLAUDE.md — tariff

Project: `tariff`
Owner: Imbra Ltd
Repository: not yet set (add the URL here when the remote exists)
Agent context file: `CLAUDE.md`

## 1. Project

`tariff` is a pricing and invoicing web application for Imbra Ltd. It holds a product catalog, discount rules of several kinds, tax jurisdictions and customers, and assembles invoices from them.

Two actors use it:

- **The administrator**, the only account, works in a browser.
- **Another program** imports the pricing engine as a library and consumes invoice exports.

The web application is one caller of the engine. The engine MUST work without the web application present.

The program's interfaces are the library's own API and the invoice exports. Nothing reaches the network. The store is a local SQLite file. The application runs locally, with no deployment target.

Customers are people. The store holds their name, email and postal address, and invoices name them. The business is in the EU, so the GDPR applies. A customer may ask for their data to be erased or for a copy of it, and the application MUST be able to do both (section 7).

## 2. Stack

| Concern | Choice |
| --- | --- |
| Language | Python 3.12 |
| Web framework | Flask 3, application factory, blueprints |
| Templates | Jinja2 with autoescape, server-rendered |
| Interactivity | HTMX 2.x, vendored under `static/` and never loaded from a CDN |
| Store | SQLite, one local file |
| Packaging | uv, with `pyproject.toml` and a committed `uv.lock` |
| Lint and format | ruff (`ruff check`, `ruff format`) |
| Types | mypy `--strict` |
| Cognitive complexity | complexipy |
| SAST | bandit |
| Tests | pytest with pytest-cov |
| Secrets | gitleaks, in pre-commit and CI |
| Hooks | pre-commit |

Not adopted, each with a revisit trigger:

| Candidate | Why not | Revisit when |
| --- | --- | --- |
| Containers, CI/CD deploy stages, IaC, Kubernetes | There is no deployment target. | A deployment target is chosen. |
| Feature flags | Nothing is rolled out progressively. | A second operator or environment exists. |
| Messaging and background jobs | Nothing is asynchronous. | An operation exceeds one request's budget. |
| Alpine.js | HTMX and plain HTML cover current needs. | Client-only state beyond a single toggle appears. |
| Distributed tracing | It is a single local process. | The application is split into more than one process. |
| Mutation testing | The suite is not yet mature. | The engine's suite is stable and its rules carry real money. |

Declining a candidate needs at most a line in the PR. It needs no ADR or ticket.

## 3. Project structure

`README.md` is the single source of truth for the directory tree. This section holds only the placement rules for agents.

- `src/tariff/engine/` is the pricing engine library. It holds the catalog model, discount rules, tax calculation, invoice assembly, exports and the public API in `__init__.py`.
- `src/tariff/store/` holds SQLite access (repositories, unit of work) and migrations.
- `src/tariff/web/` holds the Flask factory, blueprints per domain, templates and static files.
  - Blueprints: `catalog`, `discounts`, `tax`, `customers`, `invoices`, `auth`.
  - Partials live in `templates/partials/`.
- `tests/` holds `unit/`, `integration/` and `e2e/`, plus `tests/component/` for route-level tests.
- `examples/` is optional. If created, it needs its own `README.md` and follows section 13.
- `docs/` holds `ONBOARDING.md`, `PLAYBOOK.md`, `dev-journal.md` and `decisions/`.

### The boundary that must not be crossed

- `tariff.engine` MUST NOT import `flask`, `werkzeug`, `jinja2`, `tariff.web` or `tariff.store`. The engine depends on nothing but the standard library and its own modules.
- The engine receives data through parameters and protocols (for example a `CatalogReader` protocol) that `store` and `web` implement. This is dependency inversion.
- `tariff.store` MUST NOT import `tariff.web`.
- The web layer depends on both the store and the engine. It calls the engine and never re-implements pricing.

Check this after committing. Pass condition: it prints the module count, then `layering violations: 0`, and exits zero.

```bash
py - <<'EOF'
import ast, pathlib

ROOT = pathlib.Path("src")
FORBIDDEN = (
    ("tariff.engine", "flask"),
    ("tariff.engine", "werkzeug"),
    ("tariff.engine", "jinja2"),
    ("tariff.engine", "tariff.web"),
    ("tariff.engine", "tariff.store"),
    ("tariff.store", "tariff.web"),
)

def imported(tree):
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names

files = sorted(ROOT.rglob("*.py"))
print("modules inspected: %d" % len(files))
findings = []
for path in files:
    module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
    for name in imported(ast.parse(path.read_text(encoding="utf-8"))):
        for importer, banned in FORBIDDEN:
            if module.startswith(importer) and (
                name == banned or name.startswith(banned + ".")
            ):
                findings.append("%s imports %s" % (module, name))
print("layering violations: %d" % len(findings))
for finding in findings:
    print("  " + finding)
raise SystemExit(1 if findings or not files else 0)
EOF
```

A count of zero modules is a failure. It means the enumeration reached nothing.

## 4. Off-limits paths

These MUST NOT be modified without a proposal first. The proposal carries a rollback strategy and the tests that would catch a regression. The approval covers that plan, not the area.

- Auth and session code (`tariff/web/auth/`, session configuration, the password hash and login flow).
- Schema migrations (`tariff/store/migrations/`). Never edit a merged migration.
- `.env*` and anything handling secrets. This includes the secret key and the administrator credential.
- The personal-data erasure and export code (section 7). A defect there is a GDPR defect.
- The public API of `tariff.engine` (`__init__` exports) and the invoice export formats. Both are observable interfaces (section 12).
- CI workflow definitions (`.github/workflows/`), if and when they exist.

A diff touching one of these paths MUST say so at the top of its summary, naming the path, whether or not it owes a proposal. A diff confined to comments and prose is ordinary work. A `# noqa` or `# nosec` line is executable, and so is one that touches a comment and a step.

## 5. Commands

```
uv sync --locked                                 # install from the lock
uv run flask --app tariff.web run --debug        # run locally on 127.0.0.1
uv run pytest                                    # fast tier: unit + integration
uv run pytest --cov=tariff                       # with coverage
uv run ruff check src tests                      # lint
uv run ruff format --check src tests             # format check
uv run mypy src tests --strict                   # types
uv run complexipy src                            # cognitive complexity
uv run bandit -r src                             # SAST
pre-commit run --all-files                       # every hook
```

Before every commit, run pytest, mypy, ruff and pre-commit, and read the output. A local run is evidence about one platform.

## 6. Configuration

- All configuration comes from environment variables with the `TARIFF_` prefix (for example `TARIFF_DATABASE_PATH`, `TARIFF_SECRET_KEY`, `TARIFF_PORT`).
- `.env.example` is committed with placeholders. `.env` is gitignored.
- One typed `Settings` object is built once in `create_app` and passed explicitly. There are no config globals in engine or service code.
- Required settings that are missing or invalid fail at startup with a message naming the setting.
- The secret key and the administrator credential are required and have no default.
- The engine reads no environment variable. Its configuration (rounding policy, currency) is passed in.
- Bind to `127.0.0.1` by default. The port comes from `TARIFF_PORT`. Binding to another interface needs an explicit setting and an explicit decision.
- Config precedence is default, then file, then environment, then CLI flag. An empty value is an error, not a fallback to the default.

## 7. Personal data (GDPR)

Personal data means a customer's name, email and postal address, wherever they appear: the store, invoices, exports, logs, test fixtures and error messages.

- **Minimise.** Store only the personal fields the product needs. Add a new personal field only with a stated purpose in the PR.
- **Export.** One function in the store layer produces a complete copy of one customer's data (record and invoices naming them) as JSON, in a machine-readable form. It is reachable from the administrator's UI. Tests assert that every personal column in the schema appears in the export, so a newly added column fails the test until it is exported.
- **Erasure.** One function erases or anonymises one customer's personal fields in a single transaction.
  - Invoices already issued keep their amounts, tax lines and numbering, but the customer's name and address on them are replaced by a non-identifying placeholder that keeps the invoice referentially intact.
  - Whether Imbra's tax or accounting retention duty requires keeping the issued name for a period is a decision for the owner. Until an ADR records it, anonymise and do not hard-delete invoices.
  - Tests assert that no personal value survives in any table or export after erasure. This includes free-text fields and any audit or history table.
- **No personal data outside the store.**
  - Never log names, emails or addresses. Log customer ids only.
  - Error responses do not echo personal data.
  - Fixtures and examples use synthetic data only. Never copy a real customer into a test.
  - Exports and any file the app writes outside the SQLite file are written only where the administrator asks, and the UI says so.
- **The SQLite file** lives outside the repository (path from `TARIFF_DATABASE_PATH`) and is gitignored. Never commit a database file, dump or backup. Treat every repository as public.
- **Backups** of the file contain personal data. The playbook names where they go and that an erased customer reappears if a pre-erasure backup is restored, so the erasure is re-applied.
- Changing what is collected, how erasure behaves or the export shape is an observable change. It needs an ADR (section 12) and a `CHANGELOG.md` entry.

## 8. Security

There is one administrator and no other account. No network access is expected, but the application is still an authenticated web application.

- **Authentication.**
  - The administrator's password is stored hashed with scrypt (Werkzeug `generate_password_hash`) or Argon2. Never store it plain, and never use MD5, SHA-1 or plain SHA-256.
  - Compare secrets in constant time.
  - Throttle failed logins.
  - Login errors say "invalid credentials" and nothing more.
  - Every route except the login page and the health endpoint requires the session. Apply the check in one `before_request` guard on the app, not per route, so a new blueprint cannot forget it.
- **Sessions.** Cookies are `HttpOnly`, `SameSite=Lax`, and `Secure` whenever the app is served over HTTPS. The session id is regenerated at login. Sessions expire after 30 minutes idle, and logout invalidates the session server-side.
- **CSRF.** The session is authenticated by a cookie, so every `POST`, `PUT`, `PATCH` and `DELETE` carries a CSRF token (Flask-WTF `CSRFProtect`, never hand-rolled). Every form renders the token. HTMX requests send it through `hx-headers` on `<body>`. `GET` never changes state.
- **Injection and XSS.** Use parameterised queries only. Never build SQL by string interpolation. Jinja autoescape stays on, and never use `| safe` or `Markup` on data that a customer or the administrator typed.
- **Headers.** Set them in one `after_request` hook: a strict `Content-Security-Policy` (no `unsafe-inline`, no `unsafe-eval`, self-hosted scripts only), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and a restrictive `Permissions-Policy`.
  - Pin static MIME types in code, because `nosniff` makes the server the sole authority.
  - Verify script execution in a real browser, not only status codes.
  - HSTS applies only if the app is ever served over HTTPS.
- **Errors.** No stack traces, paths or SQL errors reach the browser. Return a generic message, log the detail with a request id, and use RFC 9457 `application/problem+json` for JSON error responses. Debug mode is never on outside local development.
- **Nothing reaches the network.** No CDN, font, analytics or telemetry call, and no outbound HTTP client. Adding one needs an ADR. SSRF rules apply the moment a URL from input is fetched. It is not fetched today.
- **Secrets.** None in source, history, commits, PRs or conversation. An agent MUST NOT read, print or cat `.env`, key or credential files. Check presence with `test -f .env && echo exists`. If a secret is exposed, flag it, name it and recommend rotating it.
- **Dependencies.** Commit `uv.lock` and install with `uv sync --locked`. Refresh the lock deliberately and name what refreshes it. Prefer maintained dependencies, remove unused ones, and check licences before adding one. GPL and AGPL need explicit approval.
- Run bandit and gitleaks (full history in CI) on every change.

## 9. Architecture and code rules

### Layers

The order is route handler, then service function, then repository. Handlers are thin: decode the request, call a service, render or encode the response. No database access in handlers. No HTTP concerns in services.

### Money and rounding

- Amounts are `decimal.Decimal` or integer minor units, never `float`. In SQLite store integer minor units, because SQLite has no exact decimal type.
- Currency codes are ISO 4217. Timestamps are stored in UTC.
- The rounding rule (mode and the step at which it applies: per line or per invoice) is one named constant, stated once and covered by tests.
- Never scatter `round()` calls.

### The engine

- It is a library. Pricing logic is pure: same inputs give the same output, with no I/O, no clock and no global state. Pass "now" in as a parameter.
- Discount rules of several kinds are a Strategy: one small class per kind behind a common protocol, so adding a kind is adding a class and a registry entry rather than a new branch.
- Rule ordering and stacking (which rules combine, and in what order) is stated in one place, documented, and tested with worked examples.
- Errors the engine raises on purpose derive from one `TariffError` base, each type also deriving from the built-in its site raised before. A test walks every `raise` in the package and fails on one outside the hierarchy. The test also asserts it saw at least one raise.
- No abstract operation declares `*args` or `**kwargs`.
- Prefer free functions for stateless logic. Use a class when it owns state.
- Composition over inheritance, and hierarchies at most two levels deep.
- No AOP or hidden interception. Cross-cutting behaviour is explicit at a visible call site.

### Public API

- `tariff.engine` exports its public API from `__init__.py`. Everything else is private. Public functions carry full type hints and Google-style docstrings.
- The API is stable, following semver. Before removing or renaming a public symbol, deprecate it with a comment naming the replacement, and remove it in a follow-up.
- A rename spanning a method and its keyword arguments is deprecated together or not at all.
- Importing `tariff.engine` has no side effects and reads no file or environment.
- A library attaches `logging.NullHandler()` to its own logger and installs no writing handler. The logger is injectable.

### Store

- SQLite through one connection factory. Foreign keys on (`PRAGMA foreign_keys = ON`) and WAL where it fits.
- Schema changes go only through versioned migrations, committed and never edited once merged. Each has an `up` and a `down`.
- Multi-step writes run in one transaction that is short and never spans a request. Timeouts are set on connections. No unbounded queries.
- Follow the data-modeling rules:
  - snake_case plural table names
  - `is_`/`has_` boolean prefixes
  - `<table>_id` foreign keys
  - a documented maximum length on text columns
  - foreign keys defined explicitly with a deliberate cascade choice
- Tests use a real SQLite file or `:memory:`. SQLite is the production engine, so this is not a substitute.

### HTMX and templates

- The server owns state. Endpoints return HTML.
- Detect HTMX with the `HX-Request` header. Return the partial for HTMX requests and the full page otherwise.
- Return `204` when nothing changes on screen. Return `422` with the re-rendered form and inline field errors on validation failure. Never redirect to a blank form after a failed `POST`.
- Every HTMX interaction sets `hx-target` and `hx-swap` explicitly. Use `hx-push-url` only on real navigation.
- Use `hx-indicator` and `hx-disabled-elt` on submits so nothing is submitted twice.
- Pages work without JavaScript, and HTMX enhances them.
- Partials are named for what they render (`partials/invoice_lines.html`) and take all data as explicit context. Keep at most two or three OOB targets per response.
- Templates hold conditionals and loops only. No business logic. Keep one template per view and extract repeated markup.
- Accessibility target: WCAG 2.1 AA. Use semantic HTML, labelled fields, `:focus-visible`, and full keyboard operation.

### Validation and requests

- Validate at the boundary with a schema (Pydantic or an equivalent), allowlisting rather than blocklisting. Internal code trusts validated data.
- Parse typed query parameters explicitly, so absent, valid and invalid are three distinct states. Invalid means `400`, never a silent default.
- URLs use lowercase hyphenated nouns, plural collections, nested sub-resources, no trailing slash, and camelCase query parameters.
- List views are paginated.

### General quality

- DRY, KISS, YAGNI. Every deferral names its revisit trigger.
- Names are the documentation. Functions take a verb, classes a noun, booleans `is_`, `has_` or `can_`. Use no single-letter names except loop counters and `e` in `except`.
- No boolean flag parameters. Use two named functions or an enum.
- Cognitive complexity is at most 15 per function, and nesting at most three levels. Use guard clauses.
- Magic numbers and strings become named constants. A threshold sized from data records its data source.
- No circular dependencies. Shared logic moves to a third module, never a local copy.
- Fail fast at boundaries. Fail loudly rather than fall back to a derived value.
- Every wait on another thread, process or connection is bounded and reports why it gave up.
- No dead code, no commented-out code, no debug `print`, no `pdb`. Debug tooling sits behind a flag.
- A workaround comment naming a rejected mechanism is a prompt to grep the codebase for that mechanism.
- Comments are for intent the code cannot express. Never cite a ticket, PR or ADR number in a code comment. A block comment sits directly above its item, and a trailing comment is only a tool directive.
- Identifiers are ASCII. Files are UTF-8 with LF endings. Commit `.editorconfig` and `.gitattributes` (`* text=auto`). A program that writes text sets its encoding and line ending explicitly at the boundary.
- A destructive operation (delete, truncate, overwrite) acts only on what it can prove it created. Erasure (section 7) deletes by key, never by a broad filter.
- Probe scripts are named `probe_*.py` and deleted before the commit that uses their findings.

## 10. Testing

- The fast tier (unit and integration) is the default `pytest` run. The tier follows from the directory, set by one collection hook. The e2e tier is opt-in behind a marker.
- **Unit:**
  - Engine logic is tested with pure inputs and no mocks.
  - Cover each discount kind, stacking and ordering, each tax jurisdiction, rounding edges, zero and negative quantities, and empty invoices.
  - Use worked examples with hand-computed expected totals from the business rules, not values produced by the code under test.
  - Use `pytest.mark.parametrize` for data-driven cases.
- **Integration:** real SQLite. Cover repositories, migrations up and down, and the erasure and export functions.
- **Component:** Flask test client per route. Cover success, `400`/`422` validation, `401` or redirect when unauthenticated, `404`, missing CSRF token rejected, and the partial versus full page split on `HX-Request`.
- **Engine boundary:** a test imports `tariff.engine` in a fresh interpreter with Flask blocked (for example a stub that raises on import) and exercises the public API.
- **Export contract:** each invoice export format is asserted against a fixed reference file. A round trip through our own writer and reader proves only self-consistency.
- **GDPR tests:** as in section 7. They assert that erasure and export cover every personal column.
- **Negative assertions** assert their inputs were reached. Assert the count of files, rows or records examined, not only that a set is empty.
- Tests are independent, share no mutable state and set environment variables explicitly per test. A test never touches host state outside the working directory.
- Never skip or weaken a failing test without a documented reason. A change that deletes or loosens an existing test states why. A change that adds tests needs no ceremony.
- Coverage is at least 80% overall and at least 90% of new code. It must not regress. Name the `omit` list, and adding to it is a reviewable decision.
- A test asserting a numeric threshold names what it pins.
- A visual or template change is verified against the rendered page, not the source.
- Verify a fix fires on real data, not only on a synthetic case.

## 11. Quality gates

Every category runs at three layers. CI is the backstop and duplicates pre-commit, because hooks can be bypassed.

| Category | Editor | Pre-commit | CI |
| --- | --- | --- | --- |
| Lint (ruff) | yes | yes | yes |
| Format (ruff format) | yes | yes | yes |
| Types (mypy strict) | yes | yes | yes |
| Secrets (gitleaks) | | yes | yes |
| File hygiene | | yes | |
| SAST (bandit) | | | yes |
| Cognitive complexity (complexipy) | | | yes |
| Tests and coverage | | | yes |
| Layering check (section 3) | | | yes |

- Thresholds: zero lint, format and type errors, and zero high or critical findings. Coverage is at least 80%.
- Ruff `D` rules use the Google convention, exempt for `tests/**`. Configuration lives only in `pyproject.toml`.
- mypy runs `--strict` from the first commit. Never weaken it globally. Scope an escape for an untyped third-party library to a per-module override with a stated reason.
- Site-local suppressions name the rule (`# noqa: B017`) and are never bare. The reason sits on the line above.
- When a gate is red, fix the source. Never narrow the gate, and never edit the input a check reads to make a finding disappear. Freeze existing instances by name only, never by count.
- A check states what it inspected as well as what it found, and its exit status carries its verdict.
- A skipped check is not a passed check.
- If a repository host enforces branch protection, CI checks are required status checks and bind administrators.
- CI runs the same Python version that `.python-version`, `requires-python` and mypy's `python_version` name (3.12), so every gate validates the runtime that runs the app.

## 12. Git, documentation and decisions

### Git

- Always work on a branch and never commit to `main`. Branch names are `feat/…`, `fix/…`, `chore/…` or `docs/…`.
- Commit messages use conventional prefixes (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `style:`, `test:`), the imperative mood and a subject under 80 characters. When a single-commit branch closes an issue, the subject carries the issue reference.
- PRs are small, with one concern each. Test locally, then read the CI run before calling the change good. Repeat the closing keyword before each issue number, and never write a closing keyword next to a number you only mean to reference.
- Never force-push, including `--force-with-lease`. Merge `main` into a stale branch, then regenerate any derived artifact.
- Regenerate derived artifacts in the same change that edits their source.
- Do not commit build output, `.venv/`, `__pycache__/`, `.mypy_cache/`, `*.db`, `*.sqlite*`, exports containing personal data, or `.env`. Commit the lockfile. `.gitignore` exists from the first commit.
- Before merging, review the diff in priority order: security, correctness, clarity, conventions. Personal-data handling is part of security.
- Tags are annotated `vX.Y.Z` and follow semver. A patch means fixes only, a minor adds compatibly, and a major breaks the API or an export format.

### Documentation

- `README.md` follows the nine-section structure: title and summary, features, quick start, usage, project structure, development setup, configuration reference, links, licence last. It is the source of truth for the directory tree.
- `docs/ONBOARDING.md` has six numbered sections in order: prerequisites, first-time setup, verify the setup, key files, project context, daily workflow.
- `docs/PLAYBOOK.md` has five numbered sections in order: git workflow, domain operations (add a discount kind, add a tax jurisdiction, add a personal field, run an erasure or export), quality, maintenance, release and deploy. Release and deploy stays last, and here it means tagging and publishing the library. There is no deployment.
- `docs/dev-journal.md` is required. Session entries run oldest first, with the heading `## YYYY-MM-DD — Short theme`. Each records Tool, Key changes, PRs merged, Issues closed/created, and Lesson. A P0 or P1 fix or an incident adds a post-mortem.
- Update the relevant document before every commit. No document states a count or figure about the tree outside a generated block.
- Rules use RFC 2119 words. Write in the present tense, wrap Markdown at the width declared once in configuration, and write for a reader who lacks context.
- `CHANGELOG.md` follows Keep a Changelog, with an `Unreleased` section maintained by the change that causes each entry. Entries are at most 40 words and say what changed and what a reader must do. A breaking change names the migration.
- **ADRs.** A decision needs an ADR in `docs/decisions/` (`NNN-slug.md`, YAML frontmatter, supersession through the frontmatter only) when it changes something observable without reading the internals. Here that means:
  - the engine's public API
  - the invoice export formats
  - discount stacking and rounding semantics
  - what personal data is kept, and how erasure or export behaves
  - any new outbound network path

  Tool choices, layout and process end in the PR. An ADR is not edited once merged, except for format-only changes.
- When a document disagrees with the system, establish which is wrong before changing either.
- Adopting shared rules:
  - Templates supply candidate conventions, and the project chooses what it adopts.
  - A template update creates no compliance work by itself.
  - Rules already adopted here stay in force until this project changes them.
  - Declining a new candidate needs no ADR or ticket.

## 13. Examples

If an `examples/` directory is created, one file shows one pattern or journey, for instance pricing a basket through the library without the web app.

- The directory has its own `README.md`, and each example appears there as an exact command with real output.
- Examples run offline against the project's own code and synthetic data.
- Examples are excluded from any built package, and CI runs each one after a plain `uv sync`.
- An example that verifies something exits non-zero on failure.

## 14. Working with the agent

- **Plan before implementing.** For a feature or a non-trivial change, first give the files to touch, the function signatures, the edge cases and the assumptions. Wait for approval before writing implementation code. Single-line fixes, typos and fully specified changes are exempt. If a constraint invalidates an approved plan, stop and re-surface the options.
- **Verify an issue before implementing it.** Re-read the target for existing coverage, check whether an open PR already closes it, and check for ADRs accepted since it was filed.
- **Verify a finding before reporting it.** Reproduce the defect, or label the finding unverified. A finding from a subagent is a lead, not evidence.
- **Report faithfully.** If tests fail, say so with the output. If a step was skipped, say that.
- **Ask before hard-to-reverse or outward-facing actions.** That includes anything that deletes data, touches the real SQLite file, or sends anything anywhere. Nothing may reach the network.
- **Never use real personal data.** Use synthetic customers in tests, fixtures, examples, docs and conversation.
- **End-of-session audit.** Before ending a session that changed code:
  1. Run the full gate set from section 11.
  2. Run the layering check from section 3.
  3. Confirm the docs and `CHANGELOG.md` reflect the change.
  4. Confirm that no personal data, secret or database file is staged.
  5. State what was and was not verified.

<!-- Generated with solid-ai-templates (github.com/braboj/solid-ai-templates) -->
