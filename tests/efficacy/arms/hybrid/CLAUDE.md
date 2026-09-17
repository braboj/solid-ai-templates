# CLAUDE.md

## 1. Project overview

`tariff` is a pricing and invoicing application built for Imbra Ltd. It
maintains a product catalog, several kinds of discount rules, and tax
jurisdiction data, and assembles invoices from them. The system has two
independent interfaces rather than one: a web UI for a person, and a
Python library API for another program. Both are read as first-class
consumers — neither is a thin wrapper around the other.

- **Owner:** Imbra Ltd
- **Repository:** not yet hosted — treat this file as the source of
  truth until a remote exists
- **Output file:** `CLAUDE.md` (Claude Code)
- **Rule model:** hybrid — this file inlines the rules that are
  critical or safety-relevant for this project and references the
  vendored template chain for the rest (see §12)

## 2. Stack

- Language: Python 3.12
- Web framework: Flask 3
- Templates: Jinja, with HTMX 2.x for partial-page interactivity
- Storage: SQLite — a single local file, no database server
- Package manager: uv
- Lint / format: ruff
- Type checker: mypy (strict)
- Test runner: pytest
- Deployment target: **none** — the application runs locally only

## 3. Boundaries and actors

Two actors use this system, and the architecture is built around
keeping them independent:

- **A person, working in a browser.** Served by the Flask/HTMX web
  application (`tariff.web`), which renders the catalog, discount
  rules, tax jurisdictions, and invoices as HTML and HTML fragments.
- **Another program.** Imports the pricing engine (`tariff.engine`)
  directly as a Python library, with the web application entirely
  absent. This MUST keep working with Flask uninstalled or unimported.

`tariff.web` is one caller of `tariff.engine` — not the other way
round. Business logic (catalog lookups, discount evaluation, tax
calculation, invoice assembly) lives in `tariff.engine` and MUST NOT
import anything from `tariff.web`.

The store is a local SQLite file. Nothing in this system reaches the
network: no outbound HTTP calls, no third-party APIs, no telemetry, no
CDN-hosted assets. Rules in the vendored chain written for a
network-facing service (transport security, CORS, SSRF egress
allow-listing, distributed tracing) do not apply here and are declined
in §11 — but rules protecting the browser actor from a hostile local
page (CSRF, output escaping, input validation) still apply, because the
threat model for a browser talking to `localhost` is not "the network
is trusted," it is "other tabs and other local processes are not."

The system's only two supported interfaces are:

1. **The engine's Python API** — the contract the other-program actor
   depends on.
2. **The invoice export formats** the engine produces.

A breaking change to either is an architectural decision under
`docs/solid-ai-templates/templates/base/core/docs.md` ("Decision
logs") and MUST get an ADR in `docs/decisions/`.

## 4. Project structure

```
src/
  tariff/
    engine/            # the pricing library -- importable with tariff.web absent
      catalog.py        # product catalog
      discounts.py       # discount rules (several kinds)
      tax.py              # tax jurisdictions
      invoicing.py         # invoice assembly
      export.py             # invoice export formats -- the library's other interface
      errors.py              # TariffError hierarchy (see SS8)
    web/                # Flask application -- one caller of engine/, never the reverse
      __init__.py        # create_app application factory
      config.py
      extensions.py
      blueprints/
        catalog/
        invoices/
      templates/
        partials/          # HTMX fragment responses
      static/
data/                  # editable content: tax rates, discount definitions, catalog seed data
migrations/            # versioned SQLite schema migrations
tests/
  engine/
  web/
examples/
  README.md
  standalone_invoice.py  # demonstrates importing tariff.engine with tariff.web absent
docs/
  solid-ai-templates/
    templates/            # vendored rule chain -- see SS12
  ONBOARDING.md
  PLAYBOOK.md
  dev-journal.md
  decisions/
pyproject.toml
README.md
CLAUDE.md
```

`README.md` is the single source of truth for the full structure — see
`docs/solid-ai-templates/templates/base/core/docs.md`. This section is a
pointer to it plus the one placement rule specific to agent work: new
pricing logic goes in `engine/`, never in `web/`; new HTTP-only concerns
(routing, request parsing, session handling) go in `web/`, never in
`engine/`.

## 5. Off-limits paths

These paths MUST NOT be modified without a proposal, a rollback strategy,
and named test coverage, per
`docs/solid-ai-templates/templates/base/core/git.md` ("Off-limits paths"):

- `migrations/` — schema changes are data-loss-capable
- `.env*` and any file holding the Flask `SECRET_KEY` or other secrets
- CI workflow definitions, if and when any are added under `.github/workflows/`
- `docs/solid-ai-templates/templates/` — the vendored rule chain this file
  is built from; editing it changes the rules governing the whole
  project

The default off-limits set also names auth/session code and
payment/billing code. Neither exists in this project: there is no
authentication subsystem (single local user, no login) and no payment
processor (this is a pricing/invoicing tool, not a payment gateway), so
those two categories are dropped rather than mapped onto something
else. If either subsystem is added later, add it back here in the same
change.

## 6. Session practices

### 6.1 Plan before implementing

For anything beyond a one-line fix, produce a plan (files touched,
function signatures, edge cases, assumptions) before writing
implementation code, per
`docs/solid-ai-templates/templates/base/core/review.md` ("Plan before
implementing"). Stop and resurface options if a constraint invalidates
the plan mid-implementation rather than silently re-planning.

### 6.2 Verify before reporting

A finding, a fix, or a test result is a hypothesis until demonstrated.
Reproduce a defect before reporting it; hand-check at least one
flagged item from any automated scan; confirm a check's scope before
trusting a zero. Full detail:
`docs/solid-ai-templates/templates/base/core/review.md` ("Verifying a
finding before reporting it").

### 6.3 End-of-session audit

Before ending a session that touched code, execute — do not
summarize, do not paraphrase into a bullet list — every item in:

- the **MUST checklist** and the **CI signals** checklist in
  `docs/solid-ai-templates/templates/base/core/review.md`
- the **Structure audit** section of the same file, checking every
  MUST sub-clause of `docs/solid-ai-templates/templates/base/core/docs.md`,
  `docs/solid-ai-templates/templates/base/core/readme.md`, and
  `docs/solid-ai-templates/templates/base/core/git.md` independently
- the **Documentation rule** in
  `docs/solid-ai-templates/templates/base/core/docs.md` (CLAUDE.md,
  README.md, PLAYBOOK.md, ONBOARDING.md kept in sync with the change)

Run each item against the actual diff and repository state and report
what each check found. A summary of intentions ("ran the checklist, all
good") is not a substitute for running it.

## 7. Git conventions (inlined)

Full detail: `docs/solid-ai-templates/templates/base/core/git.md`.

- Configure git with a full name and a consistent professional email —
  no personal addresses.
- Conventional commit prefixes (`feat:`, `fix:`, `chore:`, `docs:`,
  `refactor:`, `style:`, `test:`), imperative mood, subject line under
  80 characters.
- Always work on a branch — never commit directly to `main`. Branch
  naming: `feat/…`, `fix/…`, `chore/…`, `docs/…`.
- No hosted CI exists yet (see §11). Until one is wired up, tests
  (`uv run pytest`), type checking (`uv run mypy src/ --strict`), and
  linting (`uv run ruff check`) MUST be run locally before every commit
  that touches `src/` or `tests/`. Revisit trigger: wire up hosted CI
  the moment a remote repository exists or a second contributor joins,
  and drop this substitution.
- Never force-push. Delete merged branches (remote and local) and pull
  `main` afterward.
- Squash-merge safety, off-limits-path handling, and the review
  priority order (security → correctness → clarity → conventions) all
  apply as written in the vendored file — nothing about this project
  changes them.
- `.gitignore` MUST exclude `.venv/`, `__pycache__/`, `*.egg-info/`,
  `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `.env`, and the
  runtime SQLite file (e.g. `instance/tariff.db`). `data/` (tax rates,
  discount definitions, catalog seed data) and `migrations/` ARE
  tracked — they are source, not runtime state.
- Commit messages touching `data/` MUST state what changed and why
  (e.g. "fix: correct VAT rate for jurisdiction DE — statute updated
  2026-01-01"), per the data changelog rule in §9.

## 8. Python safety rules (inlined)

Full detail: `docs/solid-ai-templates/templates/base/language/python.md`.

- `ruff` is the single lint and format tool; `mypy --strict` is
  non-negotiable for both `engine/` and `web/`. No `Any` in public API
  — `tariff.engine`'s public surface is the contract the other-program
  actor depends on, and an untyped hole in it is a hole in that
  contract.
- All tool configuration lives in `pyproject.toml` — no `setup.cfg`,
  no `tox.ini`.
- Every exception `tariff` raises on purpose MUST derive from a single
  package base (`tariff.engine.errors.TariffError`), and each concrete
  type MUST also derive from the built-in its site previously raised.
  Distinguish by whether a caller could act differently:
  `CatalogError`, `DiscountError`, `TaxJurisdictionError`,
  `InvoiceError` — not one exception class per raise site.
- `tariff.engine` MUST attach only `logging.NullHandler()` to its own
  module logger and install no writing handler — it is a library, and
  a library that writes to stdout on import breaks the other-program
  actor's own logging setup. `tariff.web` MAY configure a writing
  handler at its own entry point.
- No debug `print()`, no commented-out code, no hardcoded breakpoints
  in committed code, per
  `docs/solid-ai-templates/templates/base/core/quality.md` ("Debug
  code").
- SQLite is accessed through the standard library `sqlite3` module or a
  thin repository layer — no ORM is currently justified for a
  single-file local store; introduce one only when the repository layer
  itself becomes the bottleneck (YAGNI revisit trigger).
- No parameter string-building for SQL — parameterized queries only,
  per `docs/solid-ai-templates/templates/backend/database.md` and
  `docs/solid-ai-templates/templates/base/security/security.md`
  ("Injection prevention").

## 9. Data and content rules (inlined)

Full detail:
`docs/solid-ai-templates/templates/base/data/data-modeling.md` and
`docs/solid-ai-templates/templates/base/data/data-quality.md`.

This project's "content" is its pricing data — the product catalog,
discount rules, and tax jurisdiction tables that drive every invoice.
Getting this wrong produces a wrong invoice, so these rules are treated
as safety-relevant, not decorative:

- All editable pricing content (tax rates, discount definitions, catalog
  seed data) lives under `data/` — never hardcoded inside
  `engine/*.py`. A tax rate embedded in a function is a stale tax rate
  waiting to happen.
- Every tax rate and discount rule MUST trace to a named source (a
  statute, a published rate table) and record when it was last
  verified. Undocumented, guessed, or estimated rates are not
  acceptable in this domain.
- Explicit absence over invented values: a product, jurisdiction, or
  discount with no rate on record is `None` — never defaulted to zero,
  never extrapolated from a neighboring entry. An invoice silently
  computed against a fabricated rate is worse than one that refuses to
  compute.
- Naming: snake_case tables and columns, foreign keys as
  `<table>_id`, boolean columns prefixed `is_`/`has_`.
- Money is stored and computed as integers (cents) or `Decimal` —
  never `float`. This applies throughout `engine/` and in SQLite
  column types.
- Schema changes to `data/` or the SQLite schema are additive by
  default (add new → migrate → drop old); a destructive change without
  that sequence is a red flag in review.
- Invoice computation is deterministic: the same catalog + discount
  rules + tax rates + line items MUST always produce the same invoice.
  Pin this with golden/characterization tests over representative
  invoices (see
  `docs/solid-ai-templates/templates/base/core/testing.md`,
  "Prove a behaviour-preserving refactor with a fingerprint") so a
  refactor of `engine/` cannot silently change a total.
- A change to `data/` is committed with a message stating what changed
  and why (see §7) — no batching unrelated rate or catalog changes into
  one commit.

## 10. Referenced, not inlined

These are adopted in full but not reproduced here — read the vendored
file when working in the relevant area:

| Area | File |
| --- | --- |
| Quality bar (DRY/KISS/YAGNI, readability, maintainability) | `docs/solid-ai-templates/templates/base/core/quality.md` |
| Testing taxonomy and patterns | `docs/solid-ai-templates/templates/base/core/testing.md` |
| Peer review process and checklists | `docs/solid-ai-templates/templates/base/core/review.md` |
| OOP / SOLID / composition | `docs/solid-ai-templates/templates/base/core/oop.md` |
| Configuration (env vars, precedence) | `docs/solid-ai-templates/templates/base/core/config.md` |
| CLI/driver shape for maintenance scripts | `docs/solid-ai-templates/templates/base/core/cli.md` |
| `examples/` directory rules | `docs/solid-ai-templates/templates/base/core/examples.md` |
| README structure | `docs/solid-ai-templates/templates/base/core/readme.md` |
| Documentation (ADRs, journal, changelog) | `docs/solid-ai-templates/templates/base/core/docs.md` |
| Quality gate layers and thresholds | `docs/solid-ai-templates/templates/base/workflow/quality-gates.md` |
| HTTP/URI conventions for Flask routes | `docs/solid-ai-templates/templates/backend/http.md` |
| Database/migration conventions | `docs/solid-ai-templates/templates/backend/database.md` |
| Handler → service → repository layering | `docs/solid-ai-templates/templates/backend/quality.md` |
| Jinja templating, escaping, CSRF, partials | `docs/solid-ai-templates/templates/backend/templating.md` |
| Application security baseline | `docs/solid-ai-templates/templates/base/security/security.md` |
| HTMX attributes, partials, OOB swaps | `docs/solid-ai-templates/templates/stack/htmx.md` |
| Flask application factory / blueprints | `docs/solid-ai-templates/templates/stack/python-flask.md` |
| Library packaging and structure | `docs/solid-ai-templates/templates/stack/python-lib.md` |

There is no a11y- or SEO-specific template in this project's resolved
chain (`templates/frontend/ux.md` and the SEO sections of
`templates/frontend/quality.md` were not pulled in by any stack this
project uses). Baseline accessibility still applies through
`backend-templating`: semantic HTML, labeled form fields, and visible
focus states are expected of every Jinja template, reviewed by eye —
there is no automated a11y gate for this project. SEO rules do not
apply at all: `tariff` has no publicly indexed pages.

## 11. Adopted vs. declined

Per `docs/solid-ai-templates/templates/base/core/docs.md`
("Adopting shared rules"), this file is the adoption boundary. A newer
revision of the vendored templates does not, by itself, expand what is
adopted here — that always takes an explicit edit to this file.

**Adopted in full:** `base/core/quality.md`, `base/core/testing.md`,
`base/core/review.md`, `base/core/oop.md`, `base/core/config.md`,
`base/core/cli.md`, `base/core/examples.md`, `base/core/readme.md`,
`base/core/docs.md`, `base/language/python.md`,
`base/workflow/quality-gates.md`, `base/data/data-modeling.md`,
`base/data/data-quality.md`, `backend/http.md`, `backend/database.md`,
`backend/quality.md`, `backend/templating.md`, and the four stack files
(`python-lib.md`, `python-service.md`, `python-flask.md`, `htmx.md`).

**Adopted partially:** `base/security/security.md` — input validation,
output encoding, injection prevention, CSRF, secrets-in-code, error
handling, and logging sections apply. The transport-security, security
headers (HSTS/CSP tuned for a public site), and SSRF/CORS sections are
declined — there is no outbound traffic and no cross-origin caller to
defend against. `backend/observability.md` — structured local logging
applies; distributed tracing, span propagation, and OpenTelemetry are
declined (single process, no downstream services to trace).

**Declined, with a revisit trigger:**

| File | Why declined | Revisit trigger |
| --- | --- | --- |
| `base/infra/cicd.md` | No deployment target; no hosted pipeline to define | A remote repository or CI runner is set up |
| `base/infra/containers.md` | Runs locally, no artifact is ever shipped as an image | A deployment target is introduced |
| `base/security/devsecops.md` | Hosted SAST/DAST/SBOM/release-signing all assume a release pipeline this project doesn't have | A deployment or distribution process is introduced |
| `backend/messaging.md` | Single local process; no broker, no async workers | Background job processing across processes is introduced |
| `backend/features.md` | No multi-environment rollout; single local user, single environment | Staged rollout or multi-tenant use is introduced |

Declining any of the above needs no ADR and no separate ticket — this
table is the record.

## 12. Governing rules and template chain

The rules above are drawn from a vendored copy of the project's rule
templates, checked into this repository at
`docs/solid-ai-templates/templates/` — **not** a git submodule. Do not
add one; the copy here is already the source of truth for this
revision. To update it, replace the files under that path directly and
re-run the resolution this file was generated from.

Full dependency chain resolved for this project's stack
(`stack-python-lib` + `stack-flask` + `stack-htmx`), listed by path
under `docs/solid-ai-templates/templates/`:

```
base/core/git.md
base/core/docs.md
base/core/readme.md
base/core/quality.md
base/core/testing.md
base/core/review.md
base/core/oop.md
base/core/config.md
base/core/cli.md
base/core/examples.md
base/language/python.md
base/workflow/quality-gates.md
base/security/security.md
base/security/devsecops.md
base/infra/containers.md
base/infra/cicd.md
base/data/data-modeling.md
base/data/data-quality.md
backend/http.md
backend/database.md
backend/observability.md
backend/quality.md
backend/features.md
backend/messaging.md
backend/templating.md
stack/python-lib.md
stack/python-service.md
stack/python-flask.md
stack/htmx.md
```

## 13. Commands

```
uv sync                              # install dependencies
uv run pytest                        # run the full test suite
uv run pytest tests/engine           # run only the library's tests
uv run mypy src/ --strict            # type check
uv run ruff check src/ tests/        # lint
uv run ruff format src/ tests/       # format
uv run flask --app tariff.web run    # run the web app locally
```

<!-- Generated with solid-ai-templates (github.com/braboj/solid-ai-templates) -->
