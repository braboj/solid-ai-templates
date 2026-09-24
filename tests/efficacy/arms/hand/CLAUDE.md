# Project rules

## Layout

- `src/tariff/` for the package, `tests/` for tests, `pyproject.toml` for
  metadata and tool configuration.
- The pricing engine is pure Python and imports neither Flask nor the
  persistence layer. The web application imports the engine, never the
  reverse. Templates receive plain values, not database rows.

## Quality

- `ruff check`, `ruff format --check` and `mypy --strict` are clean.
- Tests under `pytest` cover the pricing rules, the routes and the exports,
  every boundary the spec names, and 80% of lines.
- Keep functions short and nesting shallow. Name things after the domain.

## Errors

- One exception hierarchy rooted at `TariffError`; every error the package
  raises on purpose derives from it, and validation errors name the field.
- Never swallow an exception silently.

## Web

- Escape everything rendered. Never mark untrusted text safe.
- Every POST form carries a CSRF token and is refused without one.
- Validate on the server. Return 404 for an unknown identifier, not 500.

## Security and data

- Follow OWASP ASVS level 1 for sign-in, sessions and input handling.
- Customer data is personal data under the GDPR: store only what the spec
  asks for, and honour a customer's erasure and access requests.

## Money

- `Decimal` everywhere in the pricing path. No floats. Round only where
  the spec says to round.
