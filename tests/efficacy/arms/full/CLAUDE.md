CLAUDE.md
============

# tariff

**Owner:** Imbra Ltd
**Agent context file for:** Claude Code (this file). See `README.md` for the
human-facing overview once it exists — this file is agent guidance and
project rules, not a substitute for it.

## 1. What this is

`tariff` is a pricing and invoicing engine: a product catalog, discount
rules of several kinds, tax jurisdictions, and invoices assembled from
them. It ships as a Python library with a small Flask web application
layered on top for interactive use.

The project runs locally only. There is no deployment target, no hosting
environment, and no network dependency of any kind — everything reaches
only the local filesystem (a single SQLite file).

## 2. Actors and boundaries

There are exactly two actors:

- **A person working in a browser**, via the Flask + Jinja + HTMX web
  application.
- **Another program**, which imports the pricing engine directly as a
  Python library, with no web application present.

The pricing engine (catalog, discount rules, tax jurisdictions, invoice
assembly) is a **library**. The Flask web application is **one caller of
that library**, with no special access the other-program caller lacks. Any
design that gives the web layer a shortcut into engine internals the
library API does not expose is a layering violation, not a convenience.

The two supported, stable **interfaces** of this project are:

1. The library's own public Python API (`import tariff`).
2. Invoice exports (the files/documents the engine produces).

Everything else — the Flask routes, the templates, the HTMX partials, the
database schema — is implementation detail behind those two interfaces and
may change without the same stability guarantees. Treat a change to either
interface as **architecturally significant** per §12 (Decision records):
it needs an ADR, a deprecation window (see `base-quality`'s "before
removing or renaming a public symbol, mark it deprecated"), and the same
scrutiny `backend-quality`'s API-stability rule gives a versioned HTTP API,
adapted to a Python API and a file format instead of a wire contract.

There is no third actor and no network boundary to defend: nothing in this
project makes an outbound network call, and the web application is not
exposed beyond the local machine. Rules elsewhere in this file that assume
a network-facing service (CORS, SSRF, TLS, security headers, DAST) are
declined for that reason — see §7.

## 3. Stack

| Concern | Choice |
| --- | --- |
| Language | Python 3.12 |
| Web framework | Flask 3 |
| Templates | Jinja (bundled with Flask) |
| Interactivity | HTMX 2.x, server-rendered partials |
| Storage | SQLite, single local file |
| Package manager | `uv` |
| Lint / format | `ruff` / `ruff format` |
| Type checker | `mypy` (strict) |
| Tests | `pytest` |
| Distribution | none — local checkout only |

No container image, no CI/CD pipeline, no cloud target. If a deployment
target is ever added, treat that as the revisit trigger for adopting
`base-cicd`, `base-containers`, `base-security` transport/headers rules
and `base-devsecops` — none of them are adopted now, and none of them are
declined for lack of merit; they are declined because there is nothing
here for them to protect yet.

## 4. Project structure

`README.md`, once created, is the single source of truth for project
structure (`base-docs`). This section is a pointer plus agent-specific
placement rules, not a second directory tree to keep in sync — update
README first, then bring this section's placement notes in line with it
if they diverge.

Initial layout (seed this into `README.md` § Project structure when it is
created):

```
src/
  tariff/
    __init__.py        # public library API — catalog, discounts, tax, invoices
    catalog.py
    discounts.py
    tax.py
    invoices.py
    storage.py          # SQLite access; file path is an injected setting, never a global
    web/                 # Flask application — imports tariff, never the reverse
      __init__.py        # create_app() factory
      blueprints/
        catalog/
        discounts/
        invoices/
      templates/
      static/
tests/
  test_catalog.py
  test_discounts.py
  test_tax.py
  test_invoices.py
  component/            # Flask handler-level tests
  integration/           # tests against a real SQLite file
examples/
  README.md
  price_and_invoice.py   # uses `tariff` directly, no Flask installed
data/                    # local SQLite file lives here at runtime (gitignored)
pyproject.toml
.env.example
README.md
CLAUDE.md
```

Placement rules:

- `src/tariff/__init__.py` MUST NOT import anything from `src/tariff/web/`.
  The dependency runs one way: web depends on the engine, never the
  reverse (`base-quality`'s acyclic-dependency and directional-boundary
  rules). This is the mechanical form of "the web application is one
  caller of it."
- Flask, Jinja, and HTMX-related code and templates live only under
  `tariff/web/`. The engine package (`tariff/catalog.py`,
  `discounts.py`, `tax.py`, `invoices.py`, `storage.py`) MUST be
  importable and usable with no web dependency installed — this is what
  lets "another program" import the pricing engine without the web
  application present.
- Declare `web` as an optional dependency group in `pyproject.toml`
  (Flask, Jinja, HTMX static assets), so the core install stays free of
  it (`base-python-optional-deps`). `import tariff` MUST succeed in an
  environment with only the core group installed.
- `examples/` MUST contain at least one runnable example that imports
  `tariff` directly with no Flask/web dependency present, to make the
  "library usable without the web application" contract obvious and
  keep it honest (`base-examples`).

## 5. Adopted conventions and precedence

This file inlines the conventions this project has adopted from its
template chain (`stack-flask` + `stack-htmx`, over `python-service`,
`python-lib`, and the base quality/git/testing/security/docs templates).
The full candidate set is much larger than what follows — declining a
candidate here required no ADR and needs none to decline later, per
`base-docs`'s "Adopting shared rules": templates supply candidates, not
obligations.

- **This file is authoritative.** Where a rule below narrows, or
  explicitly declines, something a template would otherwise imply, this
  file governs. A future template update does not silently re-expand an
  adopted rule set here.
- Rules are adopted because they address a defect risk this project
  actually has (money-adjacent arithmetic, a public library contract, a
  local data file that must not corrupt) — not by default inheritance.
- Declined wholesale, with the revisit trigger stated: CI/CD pipeline
  rules (`base-cicd`), container rules (`base-containers`), DevSecOps
  pipeline rules (`base-devsecops` SAST/DAST/SBOM automation),
  network-facing security rules (CORS, SSRF, TLS/HSTS, security headers)
  from `base-security`, messaging (`backend-messaging`), feature flags
  (`backend-features`), Kubernetes/orchestration. **Revisit trigger:** the
  day this project gains a deployment target, a network-facing listener
  beyond localhost, or an external service dependency. Detection: a
  person deciding to deploy it is the only thing that will notice —
  there is no automated check for "this project just got a deployment
  target."

## 6. Code quality

Adopted from `base-quality` and `base-oop`, scoped to what a small
Python codebase with one library and one thin web layer needs:

- DRY, KISS, YAGNI. A discount rule or tax jurisdiction that is not
  needed yet is not built speculatively — new rule *kinds* are added
  when a real jurisdiction or promotion needs them, not in anticipation.
- Names are the primary documentation. No abbreviations, no single-letter
  names outside loop counters. Functions are verbs (`apply_discount`,
  `assemble_invoice`); classes are nouns (`TaxJurisdiction`,
  `DiscountRule`).
- Cognitive complexity kept low; maximum nesting depth of three levels;
  early returns and guard clauses over nested conditionals.
- No boolean flag parameters on public functions — where a call needs to
  select *which* discount or tax rule applies, pass the rule object or an
  enum member named for what it does, never a `bool`.
- Errors this project raises on purpose form one hierarchy under a
  package base (`base-python-errors`): a `TariffError` root, with
  specific subtypes (`InvalidDiscountError`, `UnknownJurisdictionError`,
  `InvoiceAssemblyError`) a caller can catch meaningfully. Both the
  library caller and the Flask handlers catch from this hierarchy, never
  bare `except Exception`.
- Fail fast: invalid catalog entries, malformed discount configuration,
  or an unrecognized tax jurisdiction raise immediately at the boundary
  where they enter the system (data load, API call, form submission) —
  never propagate silently into an invoice.
- Magic numbers (tax rates, currency minor-unit factors, rounding
  precision) are named constants with the source of the figure recorded
  beside them, not scattered literals.
- No debug `print()`, no commented-out code, no hardcoded breakpoints in
  committed code.
- Comments explain *why*, never *what*; no comment cites an issue or PR
  number — name the source or reasoning instead, since code outlives the
  tracker.

Composition over inheritance for discount rules and tax jurisdictions:
model each as a small object implementing a shared protocol (Strategy
pattern from `base-oop`), not a growing inheritance hierarchy or a chain
of `if isinstance(...)` checks in the invoice assembler.

## 7. Security

Scoped down from `base-security` because nothing here is network-facing
(§2):

- **Adopted:**
  - Input validation at the boundary — every value entering from a form,
    an HTTP request, or the library's public API is validated before use
    (`security-input`). Reject with a clear error; do not silently coerce.
  - Output encoding — Jinja's autoescaping stays on; no `| safe`, no
    manual HTML construction with untrusted or computed values
    (`security-output`).
  - SQL access is parameterized (via the SQLite driver's parameter
    binding or SQLAlchemy Core if adopted) — never string-interpolated
    (`security-injection`).
  - CSRF protection on state-changing HTTP requests (`security-csrf`),
    because a browser attaches cookies to `POST`s automatically even to a
    local origin; use Flask's / an extension's CSRF middleware rather than
    hand-rolling it.
  - Secrets handling: no secrets are expected (no external service, no
    auth), but `.env.example` is still committed with placeholders and
    `.env` is gitignored, in case a future setting needs to stay out of
    source control (`security-secrets`).
  - Agent secrets handling (`security-agent-secrets`): do not print or
    log the contents of `.env` or any local config file.
- **Declined, with trigger:** CORS, SSRF protections, TLS/HSTS, security
  response headers, DAST, rate limiting, authentication/session
  management. None of these defend anything that exists here — there is
  no cross-origin caller, no outbound HTTP client, no non-localhost
  listener, and no login. **Revisit trigger:** any of those change (a
  network listener beyond `127.0.0.1`, an outbound HTTP call, a login
  screen). Detection: same as §5 — a design decision a person makes, not
  an automated signal.

## 8. Configuration

Adopted from `base-config`, scaled to a local-only app:

- Configuration (SQLite file path, Flask `SECRET_KEY` for CSRF/session
  signing, debug flag) comes from environment variables, never hardcoded.
- `.env.example` is committed with placeholder values; `.env` is
  gitignored.
- The SQLite file path is a constructor parameter of the storage layer,
  never read from a global inside `tariff/catalog.py` etc. — this is what
  keeps the library usable by "another program" with its own data file.
- Fail fast: missing required configuration (e.g. no database path
  resolvable) raises at startup, not on first use.

## 9. Data and storage

The store is a single local SQLite file — not a client-server database.
Adapted from `backend-database` and `base-data-modeling`:

- Schema changes go through migrations (Alembic, or a minimal
  hand-rolled versioned-migration script if Alembic is overkill for the
  eventual schema size) — never hand-edit the SQLite file's schema.
  Migrations are committed, one logical change per migration, and are
  never modified once merged.
- No connection pooling concerns apply (SQLite is a file, not a
  server) — but a single `sqlite3`/SQLAlchemy engine instance per
  process is still the right shape, injected into the storage layer
  rather than opened ad hoc at each call site.
- Table and column names: lowercase snake_case, plural table names,
  `is_`/`has_` boolean prefixes, `<table_singular>_id` foreign keys
  (`data-modeling-naming`).
- Monetary values are stored as integers in the currency's minor unit
  (cents), never as floating point (`data-modeling-types`). Tax rates
  and discount percentages carry a documented, fixed decimal precision.
- Invoice numbering is generated by the storage layer under a
  uniqueness constraint the database itself enforces — never computed
  in application code from a value that can race (e.g. `SELECT MAX(id)
  + 1`).

## 10. Testing

Adopted from `base-testing`, `python-lib`, and `python-service`:

- `pytest` for all tests; run `pytest && mypy src --strict` before every
  commit.
- Unit tests for the pricing engine (catalog, discount rules, tax
  calculation, invoice assembly) cover all happy paths plus edge cases:
  zero-quantity lines, stacked discounts, an unrecognized jurisdiction,
  rounding at the smallest currency unit. New engine code MUST have unit
  tests achieving at least 90% coverage before merging; the project
  targets 80% overall coverage (`quality-gates-thresholds`).
- Integration tests exercise the storage layer against a real (temporary)
  SQLite file — never a mocked database (`backend-database` testing
  rule). Each test gets its own temp file or an in-memory `:memory:`
  connection, torn down after the test.
- Component tests exercise Flask handlers end to end (request in,
  rendered HTML or HTMX partial out), asserting on meaningful content
  (headings, field labels, totals) rather than exact markup
  (`backend-templating-testing`).
- Test naming: `test_<unit_of_work>_<state>_<expected>`, e.g.
  `test_apply_discount_expired_promotion_raises_invalid_discount_error`.
- No mocks for pure functions in the engine — test with real inputs and
  real (temporary) storage; mocks are reserved for the "another program"
  integration boundary if that ever needs simulating.
- Assert against an external definition where one exists: if invoice
  totals or tax figures are checked against a published example (a
  known tax table, a hand-computed reference invoice), include at least
  one test comparing against that external reference, not only
  round-tripping the engine's own encoder/decoder (`testing-external-
  definition`).

## 11. Quality gates

Local-only, no CI, so the gate layers are editor + pre-commit; there is
no Layer 3 today (`quality-gates-layers`).

| Category | Editor | Pre-commit | Tool |
| --- | --- | --- | --- |
| Lint | should | must | `ruff check` |
| Format | should | must | `ruff format` |
| Type check | should | must | `mypy --strict src` |
| Secret detection | — | must | `gitleaks` (or equivalent pre-commit hook) |
| Tests | — | should | `pytest` |
| Coverage | — | should | `pytest-cov`, 80% overall / 90% new code |

Declined: SAST/DAST scanning, SBOM generation, container image scanning,
license-compliance automation — no CI pipeline exists to run them in, and
there is no distributed artifact to scan. **Revisit trigger:** adding a
CI workflow (even a local `pre-commit` runner is not "CI" in this sense —
a hosted pipeline is). Detection: same as §5.

`mypy --strict` applies to `src/tariff/` including the `web/`
subpackage. All public functions in `tariff/__init__.py` and its
submodules carry full type annotations and Google-style docstrings
(`base-python-tooling`, `python-lib-conventions`).

## 12. Decision records

Per `base-docs`, an ADR in `docs/decisions/` is required when a change
alters something a consumer of the two stable interfaces (§2) can observe
without reading the repository's internals:

- Any change to the public library API's shape (function signatures,
  new/removed public symbols in `tariff/__init__.py`, error hierarchy
  changes a caller might catch on).
- Any change to the invoice export format (fields, structure, or the
  file format itself).
- The choice of discount-rule and tax-jurisdiction extensibility
  mechanism, if it changes materially (e.g. moving from a Strategy
  protocol to a plugin-registry model).

Routine internal refactors, Flask route reshuffling, template changes,
and HTMX interaction details do not need an ADR — they sit behind the
stable interfaces, not in them.

## 13. Git conventions

Adopted from `base-git`, scaled down (no CI, no release automation, no
publishing target):

- Conventional commit prefixes (`feat:`, `fix:`, `chore:`, `docs:`,
  `refactor:`, `test:`), imperative mood, subject under 80 characters.
- Work on a branch, never commit directly to `main`; small, focused PRs.
- `.gitignore` covers `.venv/`, `__pycache__/`, `*.egg-info/`,
  `.mypy_cache/`, `.env`, and the runtime SQLite file under `data/`.
- Semantic versioning and a `CHANGELOG.md` are **not adopted** while
  this project has no external consumers or release cadence to serve.
  **Revisit trigger:** the day "another program" (§2) is a separate
  team/repository that needs to track compatible versions of the library
  API. Detection: someone asking "which version of `tariff` am I on" is
  the signal — there is no automated check for it.
- Full release-tagging, SBOM, and GitHub Release automation from
  `base-git`'s release process are declined for the same reason as
  versioning above, and revisit together with it.

## 14. Off-limits

Cut down from `base-git`'s default five, because this project has no
auth subsystem, no payment processing, and no CI/CD workflows to protect
yet:

- **Database schema and migrations** (`src/tariff/storage.py`'s schema
  and any migration files) — a change here can silently corrupt or
  orphan data in the one local SQLite file this project has. Propose the
  change and its rollback (a down-migration or a documented manual
  recovery step) before making it.
- **`.env*` and any file handling configuration/secrets** — never
  committed with real values; changes to what configuration is read
  from the environment are proposed before being made, per
  `base-git`'s off-limits rule.

If auth, a payment integration, or a CI/CD pipeline is added later, add
it to this list at that time — per `base-quality`'s revisit-trigger
discipline, that addition is the trigger firing, not a decision to defer
further.

<!-- Generated with solid-ai-templates (github.com/braboj/solid-ai-templates) -->
