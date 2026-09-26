# tariff — CLAUDE.md

Owner: Imbra Ltd. Pricing and invoicing web app: catalog, discounts, tax, invoices.
Stack: Python 3.12, Flask 3, Jinja, HTMX, SQLite. Tools: uv, ruff, mypy strict, pytest.
Runs locally; no deployment target; nothing reaches the network.

## Structure
- The pricing engine is a library that imports without Flask; Flask is one caller.
- Flask app uses `create_app()`, blueprints, thin routes; logic lives in services.
- Layout is in README.md; do not duplicate it here.

## Personal data (GDPR)
- Customers hold name, email, postal address; invoices name them.
- Support erasure and export of one customer's data; keep invoice totals intact.
- Never log or print personal data; never put it in fixtures, commits or errors.
- One administrator signs in; CSRF on every state-changing request.

## Code
- Money is integer cents or Decimal, never float; timestamps in UTC.
- Errors raised on purpose derive from one package base error.
- Parameterized SQL only; migrations versioned, never edited once merged.
- HTMX endpoints return partials when `HX-Request` is set; 422 on invalid forms.
- Config from environment, validated at startup; `.env` is never committed.
- Names carry meaning; no debug prints, no commented-out code.

## Quality
- Gates: `ruff check`, `ruff format`, `mypy --strict`, `pytest`; all must pass.
- Test the engine without Flask; use a real SQLite file, not a mock.
- Every public function has type hints and a Google-style docstring.

## Git
- Work on a branch, never on `main`; conventional commit prefixes, subject under 80.
- Update README, CLAUDE.md and docs in the same commit as the change.

## Off-limits without an approved plan
- Auth and session code, migrations, `.env*`, and invoice export formats.
- Propose the change with rollback and test coverage first.

<!-- Generated with solid-ai-templates (github.com/braboj/solid-ai-templates) -->
