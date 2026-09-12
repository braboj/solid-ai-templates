# Project rules

## Layout

- `src/tariff/` for the package, `tests/` for the tests, `pyproject.toml`
  for the metadata and tool configuration.
- The pricing engine is pure Python. It imports neither Flask nor the
  persistence layer. The web application imports the engine, never the
  reverse.
- Templates receive plain values, not database rows.

## Quality

- `ruff check` and `ruff format --check` are clean.
- `mypy --strict` is clean. Every public function is annotated.
- Tests run under `pytest` and cover the pricing rules, the routes and
  the exports. Aim for 80% line coverage and cover every boundary the
  spec names.
- Keep functions short and nesting shallow. Name things after what they
  mean in the domain.

## Errors

- One exception hierarchy, rooted at `TariffError`. Every error the
  package raises on purpose derives from it.
- Validation failures carry the field they are about.
- Never swallow an exception silently.

## Web

- Escape everything rendered. Never mark untrusted text safe.
- Every POST form carries a CSRF token and is refused without one.
- Validate on the server. The client is not a validator.
- Return 404 for an unknown identifier, not 500.

## Money

- `Decimal` everywhere in the pricing path. No floats.
- Round only where the spec says to round.
