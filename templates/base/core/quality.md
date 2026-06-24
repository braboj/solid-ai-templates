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

## Calibration discipline

[ID: quality-calibration]

When a tool is calibrated against reference data (test fixtures with
known-correct outputs, benchmark expected results, eval data, decision
thresholds), three failure modes silently invalidate the calibration:
suspect data treated as ground truth, the threshold tuned to mask a
broken measurement, and reference values produced by the same actor
that runs the tool. The rules below address each.

### Ground truth comes from raw artifacts, not suspect data

- When calibrating a pipeline against existing committed data, verify
  the data was not produced by an earlier version of the same pipeline
- If it was, and the pipeline has known or suspected bugs, the
  committed data is NOT ground truth — calibrating against it bakes
  the existing bugs into the new gate
- Build the calibration set from raw artifacts (source images, raw
  exports, captured fixtures), recording the verified value alongside
  each entry
- A small hand-built reference set from raw artifacts beats a large
  set carried over from a suspect pipeline

### Thresholds move, not the measurement

- When a measurement and a threshold disagree, the threshold is the
  cheaper thing to change — but ONLY after the measurement is verified
  sound
- Order of operations on disagreement: (1) verify the measurement
  against an independent check, (2) tune the threshold if the
  measurement is sound, (3) change the measurement implementation
  ONLY when steps 1 and 2 fail to resolve the disagreement
- A threshold picked from theory and never validated against data is
  not a calibrated threshold — it is a guess; tuning it against the
  data on first disagreement just hides the original guess
- This rule applies wherever measurements meet thresholds: CI quality
  gates, performance budgets, ML decision boundaries, extractor
  agreement scores

### Reference data MUST carry provenance

- Each entry in a reference set MUST record `source: agent | user |
  external` (who produced the value) and `verified: true | false`
  (whether a human has reviewed it)
- An agent MAY produce reference values to speed calibration, but
  MUST set `source: agent` and `verified: false` until the user
  reviews — the user MAY veto, replace, or accept; accepting flips
  `verified: true`
- Calibration metrics computed against the reference set MUST report
  a coverage caveat alongside the headline numbers (e.g.
  "verified: 12/40"), so unverified reference data cannot silently
  dominate the metric
- Synthetic test inputs (faker-style data, generated fixtures) are
  out of scope — this rule covers reference *outputs* compared
  against tool *outputs*, not test inputs

## Cross-validation and tool trust

[ID: quality-cross-validation]

When output is cross-validated against an external source (vendor
page, API, spec sheet, scrape), two distinct failure modes produce
misleading divergence reports: a buggy validation tool that misreads
the source, and a semantic mismatch between *stored default* and
*source silence*. Both look like "the data is wrong" and waste
maintainer time on phantom fixes.

### Verify the tool before trusting its output

- When a validation, scraping, or migration tool drives a bulk
  change, confirm the tool is correct BEFORE acting on its output
- A systematic tool bug masquerades as data divergence — applying
  the tool's values blindly corrupts correct stored data
- Treat a physically implausible output value as a tool defect:
  fix, re-run, then apply
- When the external source itself looks wrong (stale page, wrong
  record served), cross-check an independent source before
  overwriting stored data
- Applies to scrapers, importers, schema-migration verifiers, and
  lint-driven codemods — any automated diff that drives a bulk
  change

### Distinguish source-silent from source-says-false

- A stored default (e.g. `absent boolean = false`) and source
  silence (the source did not mention the field) are NOT the same
  thing — treating them as equivalent produces a flood of
  false-positive mismatches that bury real errors
- The extractor MUST return a field ONLY when the source
  affirmatively states it
- The differ MUST compare a field ONLY when present on both the
  stored and source sides — source-silence skips comparison, never
  becomes a confirmed value
- This keeps stored-default conventions (`absent = false`,
  `null = unknown`) intact while making cross-validation meaningful
- The trap is non-obvious: the stored-default convention and the
  verification semantics pull in opposite directions, and the naive
  implementation looks correct until run against real data

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

### Probe scripts

- Probe scripts are throwaway tooling: a small file that measures or
  inspects something (data shape, file structure, runtime behaviour)
  and prints findings to inform a source change
- Name them so they are obviously temporary: `probe_*.py`, `_probe.sh`,
  `scratch_*.ts`, or equivalent
- A probe script MUST be deleted before the commit that uses its
  findings — the script itself never lands on `main`
- Findings worth keeping go into source comments, ADRs, or docs —
  not the probe script
- Probe scripts are the antidote to guessing: prefer writing one
  over inferring data shape or runtime behaviour from incomplete
  evidence

## Automated enforcement

- Quality conventions in this document are enforced automatically via
  quality gates (editor → pre-commit → CI)

## Testing

- Write tests for business logic and edge cases
- Do not test implementation details — test behaviour
- Tests must pass before merging to `main`
- Tests MUST be runnable from CI without human intervention
