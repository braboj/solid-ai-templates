# Base — Quality Attributes

[ID: base-quality]

## Core principles

- **DRY — Don't Repeat Yourself**: every piece of knowledge must have
  a single, authoritative representation; the third copy is a bug
- **KISS — Keep It Simple**: prefer the simplest solution that works;
  complexity must be justified by a requirement, not by elegance
- **YAGNI — You Aren't Gonna Need It**: do not build for hypothetical
  future requirements; build what is needed now, refactor when the
  need is real. When YAGNI defers a dependency, abstraction, or
  feature, record the concrete *revisit trigger* alongside the
  deferral (e.g. "when this grows to N config values," "when this
  is extracted to its own repo," "when a second call site appears").
  A deferral without a trigger gets re-argued every time it comes up
  or quietly forgotten; a deferral with a trigger is a decision.

## Architecture

- All editable content in a data directory — never hardcoded in source modules
- Never hardcode derived counts or statistics — compute them from the data
  source; a hardcoded number is a stale number
- Default to the simplest abstraction; only reach for heavier patterns
  when genuinely needed
- No dead code — remove unused modules, assets, and data files promptly
- No over-engineering — build the minimum needed for the current requirement

## Readability

- **Names are the primary documentation** — a name that requires a comment to
  explain is a name that needs to be changed
- Functions and methods: verb or verb phrase (`calculateTotal`, `fetchUser`)
- Classes and modules: noun or noun phrase (`OrderRepository`, `AuthService`)
- Booleans: prefix with `is`, `has`, or `can` (`isActive`, `hasPermission`)
- No single-letter names except loop counters (`i`, `j`) and well-established
  conventions (`err` in Go, `e` in except clauses)
- No abbreviations unless universally understood in the domain (`url`, `id`,
  `http` are fine; `mgr`, `proc`, `obj` are not)
- A function's name must make reading its body unnecessary — if you need to
  read the implementation to understand what a call site does, the function
  needs a better name or needs to be split
- Cognitive complexity ≤ 15 per function — enforced by static analysis
  (SonarQube, Codacy, or `eslint-plugin-sonarjs` for ESLint); each
  nesting level and decision point increases the score

### eslint-plugin-sonarjs rules (if applicable)

| sonarjs rule | Enforces |
|---|---|
| `cognitive-complexity` | Cognitive complexity ≤ 15 per function |
| `no-nested-conditional` | Maximum nesting depth |
| `no-duplicated-branches` | DRY — identical branches in if/switch |
| `no-identical-expressions` | DRY — same expression on both sides of operator |
| `no-identical-functions` | DRY — duplicated function bodies |
| `no-collapsible-if` | KISS — collapse nested ifs |
| `no-redundant-jump` | No dead code — unnecessary return/continue/break |
| `no-unused-collection` | No dead code — collection populated but never read |
| `no-inverted-boolean-check` | Readability — avoid negative conditions |
- Maximum nesting depth of three levels — use early returns and guard clauses
  to reduce indentation rather than adding else branches
- No boolean flag parameters — they force the caller to read the implementation
  to understand what `true` means; use an enum or two named functions instead
- Avoid negative conditions in `if` statements where possible —
  `if isEnabled` reads better than `if !isDisabled`

## Maintainability

- No circular dependencies between modules or packages — dependency graphs
  must be acyclic; restructure or introduce an interface to break cycles
- Keep the dependency graph shallow — if changing module A requires reading
  modules B, C, and D to understand the impact, the coupling is too high
- Changes to one module's internals must not require changes in unrelated
  modules — if they do, the abstraction boundary is wrong
- Before removing or renaming a public symbol, mark it deprecated with a
  comment referencing the replacement; remove it in a follow-up change
- Magic numbers and magic strings must be named constants — unnamed literals
  scattered across the codebase are a maintenance hazard
- No substantial duplication across sibling modules — if the same code
  appears in two or more places, extract a shared module; the third
  copy is a bug
- Consistent naming across modules — the same concept must use the same
  name everywhere; divergent names for the same thing (e.g. `clearButton`
  vs `clearBtn`) signal missing abstraction
- When the same logic block repeats across three or more modules,
  extract a shared module; short inline repetition (e.g. three similar
  assignments) does not warrant extraction — only substantial
  duplicated logic
- **Fail Fast**: validate inputs at boundaries and throw immediately on
  invalid state; do not propagate bad data through the system
- **Law of Demeter**: a module should only talk to its direct
  dependencies; chaining through objects (`a.b.c.d`) signals missing
  abstraction
- **High Cohesion**: modules that change together should live together;
  a module whose parts serve unrelated concerns should be split

## Testability

- Testability is a first-class design concern, not an afterthought
- Code MUST be designed for testability from the start — do not write
  code first and struggle to test later
- If code is hard to test, treat it as a design problem, not a
  testing problem

## Code style

- Encode all source files in UTF-8; content MUST be restricted to ASCII
  characters
- Line endings MUST be LF — CRLF is not acceptable in any committed file
- A linter SHOULD enforce formatting automatically on save; keep manual style
  rules to a minimum
- Commit an `.editorconfig` file at the project root — enforces indent
  style, indent size, line endings, charset, and trailing whitespace
  across all editors without tool-specific config
- Prefer self-documenting code — if a comment feels necessary, treat it as a
  signal that the code needs restructuring before the comment is added
- Add comments only where the intent cannot be expressed in code

## Debug code

- No debug statements in committed code: no `print()`, `console.log()`,
  `fmt.Println()`, or equivalent used for debugging
- No hardcoded breakpoints (`debugger`, `pdb.set_trace()`) in committed code
- No commented-out code blocks — delete dead code; version control is the history
- Debug tooling (profilers, REPL helpers, verbose loggers) MUST be
  gated behind a flag or environment variable, never on by default

## Automated enforcement

- Quality conventions in this document are enforced automatically via
  quality gates (editor → pre-commit → CI)

## Testing

- Write tests for business logic and edge cases
- Do not test implementation details — test behaviour
- Tests must pass before merging to `main`
- Tests MUST be runnable from CI without human intervention
