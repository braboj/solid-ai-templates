# tariff — CLAUDE.md

## Project
Imbra Ltd. Pricing/invoicing web app: product catalog, discount rules,
tax jurisdictions, invoices. The pricing engine is a standalone
library — the Flask app and a second program both import it.
Local-only: SQLite file store, no network dependency, no deploy target.

## Stack
Python 3.12, Flask 3, Jinja, HTMX, SQLite. uv, ruff, mypy --strict, pytest.

## Structure
- `src/tariff/` — pricing engine; no Flask imports, runs standalone.
- `src/tariff_web/` — Flask app, the only HTTP-facing caller.
- `tests/` mirrors `src/`.

## Conventions
- Web stays thin: route -> engine call -> Jinja/HTMX render. Engine
  never imports the web layer.
- Public library API: full type hints, Google docstrings, no `Any`,
  clean under `mypy --strict`.
- Discount/tax rules are pure functions; cite the source
  (regulation/spec) for each rule in a comment.
- Centralize invoice totals/rounding in one function; never recompute
  inline — invoices are the exported contract.
- No DB access in route handlers — go through the engine.
- `ruff check`/`ruff format` gate lint and style; fix, don't suppress.

## Testing
- Engine: unit tests for 100% of public API.
- Web: per-route tests for 2xx, 400/422, 404.
- Before commit: `pytest && mypy src --strict && ruff check src tests`

## Git
Conventional commits, feature branches, PR review before merge. Never
commit `.env`, `*.db`, `__pycache__/`, `.mypy_cache/`.

## Off-limits
Tax/discount logic and invoice rounding — propose changes and get sign-off
first; errors have real financial impact. DB schema: migrations only.
