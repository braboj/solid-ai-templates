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
- **Delete dead-code paths discovered during implementation**: when a
  probe against real data invalidates a path you wrote earlier in the
  same session, delete it in the same commit. "In case it's useful
  later" is sunk-cost reasoning — what you already wrote feels valuable,
  but code with no real test case to anchor it rots fast and confuses
  the next maintainer about which path actually fires. If a future case
  needs it, git history has it. Distinct from YAGNI: YAGNI says do not
  build speculative code; this says retract what probing made speculative.

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
- When an import cycle would block sharing logic between two modules, move
  the shared logic to a third module — never code a divergent local copy
  in one caller; a silent copy drifts from the canonical version (e.g.
  skipping an upstream filter step) and breaks later, invisibly
- Keep the dependency graph shallow — if changing module A requires reading
  modules B, C, and D to understand the impact, the coupling is too high
- Changes to one module's internals must not require changes in unrelated
  modules — if they do, the abstraction boundary is wrong
- Before removing or renaming a public symbol, mark it deprecated with a
  comment referencing the replacement; remove it in a follow-up change
- When extending a function's return type (value → list, scalar → tuple),
  keep a one-line shim under the old name returning the first/scalar
  element so existing callers and tests survive; remove it in a follow-up
- Magic numbers and magic strings must be named constants — unnamed literals
  scattered across the codebase are a maintenance hazard
- Size numeric thresholds (a filter, cutoff, bound, or tolerance) from the
  actual distribution of the relevant quantity in the working data set
  (p95, p99, max-legitimate) — not from first principles or intuition. A
  threshold chosen by feel is too loose (masks bugs) or too tight (breaks
  edge cases) with no record of why. Document the data source in the
  constant's docstring so a future maintainer can rerun the analysis
  against fresh data and re-validate
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
- **Fail loud, not silent on auto-derivation**: when a value can be
  either derived algorithmically (from a slug, name, hash) or read from
  a source-of-truth field, prefer the read; when the field is missing,
  raise/error rather than fall back to the derived value. A
  wrong-but-plausible derived value (a 404 URL, a mismatched ID) emitted
  without warning is worse than a script that refuses to run until the
  data is correct
- **A caller-side input filter is not a precondition**: when a runner
  filters its inputs by a caller-side criterion (data availability,
  ground-truth presence, a feature flag) that is tighter than the inner
  function's actual preconditions, the function silently rots whenever an
  unrelated change breaks it on the excluded inputs — no test exercises
  them. Either widen the filter so the function runs over its full input
  domain, or push the precondition into the function as an assertion so
  it fails loud. A filter that "happens to" exclude broken inputs is a
  buried defect waiting for someone to lift it
- **Law of Demeter**: a module should only talk to its direct
  dependencies; chaining through objects (`a.b.c.d`) signals missing
  abstraction
- **High Cohesion**: modules that change together should live together;
  a module whose parts serve unrelated concerns should be split
- **Per-config opt-in over global auto-detect**: when an algorithm
  variant helps one input class and hurts another, prefer a per-config
  flag with a safe default over a global threshold that auto-detects
  which class an input belongs to. Auto-detect works only when the input
  cleanly partitions on a measurable signal; when it does not, it
  misclassifies silently — often for the worst input. Per-config opt-in
  captures the human-known classification directly
- **Cross-language function ports must be byte-equivalent**: when a
  function exists in one language and is consumed by code in another,
  port it exactly — same operation order, character classes, and edge
  cases (empty input, leading/trailing separators). Reference the
  original in the port's docstring so the invariant is discoverable.
  Never re-implement from the name or description alone — that produces
  close-but-diverging siblings that surface as silent data corruption
- **Decompose a ported mega-script into a strategy-dispatched
  pipeline**: when porting a procedural script (one file, branching
  control flow per case) into a typed library, split it into small
  single-responsibility modules with the orchestrator dispatching on a
  declared type-axis (enum / Literal / tagged union). Adding a case
  becomes "add a dispatch arm," not "sprinkle if-this-case throughout,"
  and each stage becomes testable in isolation — this composes the
  existing strategy and composition patterns, not a new one
- **Build extraction-ready internal modules**: structure an internal
  module today so it can become a standalone repo or submodule tomorrow
  without a rewrite. Host-specific values (cache dirs, config) MUST be
  injected as constructor parameters with portable defaults, never read
  from host globals; the module MUST own its public API (`__init__`
  re-exports), README, tests, and requirements; a thin CLI wraps the
  library rather than being the product. Extraction stays deferred, but
  the module is ready the moment it is wanted

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
- When a reference set flips from tool-seeded to independently verified
  values (the de-circularization above), grep the codebase in the same
  change for comments, guard conditions, and thresholds whose rationale
  cites the OLD data, and re-verify each against the new ground truth —
  or file an issue per survivor. The reasoning citing the stale values
  keeps steering the code long after the data is corrected; the sweep is
  one grep at a well-defined moment (the ground-truth-flip change)

### Honest absence beats a recovered wrong value

- When a fix flips an extractor from a wrong value to an honest absence
  (`None`, empty, no-reading) because the source genuinely has no data
  at that point, the absence is the correct output — not a regression
  to recover
- Update the reference / ground-truth framing in the same change: any
  prior expected value at that point MUST be re-marked as extrapolation
  past the data, never carried forward as a hit-this target the
  extractor "should" reach
- Distinguish the two absences in logs and reference notes: `None`
  because the extractor failed (a defect to fix) versus `None` because
  the source carries no value there (the correct answer) — the two
  demand opposite responses, and conflating them sends a maintainer to
  "fix" a correct absence

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

### Diagnose before tuning

- Before changing a parameter whose value was set by a calibration
  step or carries a tuning rationale, first PROBE to confirm the
  parameter is the actual constraint — do not tune-and-see
- Trace the value where it is computed and read the real intermediate
  inputs from a real sample (a probe script, or a trace-not-propose
  investigation), never a synthetic case
- Tuning is valid once the probe shows the parameter is genuinely the
  constraint; the wasteful move is changing code on "this might help"
  without probing, which burns time and risks regressing unrelated
  calibrated anchors

### Calibration aids MUST NOT depict the system's own output

- Any artifact that informs a human-verifies-machine signal (a human
  reading values from a source document, code review against a generated
  patch, audit grading against a candidate report) MUST render only the
  reference data plus the maintainer's reading guides
- The candidate output goes in a separate artifact, opened only after
  the independent reading is captured — surfacing it alongside the
  reading task biases the reading toward the candidate and turns the
  calibration into a self-confirming loop
- Name the candidate-output artifact distinctly (`*-overlay.png`,
  `*-trace.svg`, `*-prediction.md`) so it cannot be confused with the
  reading aid
- Comparison views opened AFTER the independent reading is captured
  (diff viewers, side-by-side dispute resolution) are out of scope —
  they are downstream of the signal and do not bias it

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
- Commit a `.gitattributes` at the project root with `* text=auto`
  (add `eol=lf` where the project wants hard LF) — the git-side
  guarantee that no CRLF is committed, covering files written by any
  tool, editor, or contributor without an EditorConfig plugin.
  EditorConfig normalizes editor-side only; `.gitattributes` enforces
  the LF rule at commit and checkout. Verify with `git ls-files --eol`
  — no committed file reports `i/crlf`
- Prefer self-documenting code — if a comment feels necessary, treat it as a
  signal that the code needs restructuring before the comment is added
- Add comments only where the intent cannot be expressed in code
- A comment that explains *why* something is safe ("X holds because Y") is a
  load-bearing claim, not documentation — re-verify it against current data the
  next time the code is read, never rely on it as-is. Reasoning comments rot
  faster than the code they annotate: the code stays correct while the predicate
  the comment cites silently goes false
- A comment or doc note that cites an issue, PR, or ADR by number inherits
  that reference's lifecycle: when the cited item is closed without action,
  superseded, or replaced by a different fix, the citation is a defect even
  when the annotated code still works — a future reader tracing the stale
  number lands on a dead thread and misses the live follow-up. Fix it in a
  small change. When closing or superseding an item that comments may cite,
  audit the references in the same change — `rg "#<number>"` (or the tracker
  URL) over the repo lists them, and the audit is done when none point at the
  stale item
- In code comments and docstrings, go further: never cite a ticket, PR,
  or ADR *number* at all — code outlives the tracker, so state the
  substance instead (name the descriptor, source, or derivation, not
  "see #123" or "per ADR 0002"). Markdown docs (README, ADRs, the dev
  journal) are the opposite: cross-referencing issues and ADRs by number
  is their job. One exception in code: non-obvious or scientific logic
  MAY name a *source* (author + year + method — "Rappé 1992"), which
  ages gracefully where an issue number does not. Enforce with a test
  that greps comments/docstrings for `#\d+` / `ADR\s*\d+`
- A block comment MUST sit directly above the item it documents: never
  trailing to the right of code (tool directives like `# noqa` / `# nosec`
  are excepted), and never separated from that item by a blank line
- Separate each comment-plus-item group from the next with a single blank
  line, so the comment and the lines it explains read as one unit
- Wrap comment prose to the project's configured line-length limit, the same
  limit as code. Enforce this for commented configuration files
  (`pyproject.toml`, YAML, CI workflows) too, even where the linter does not
  scan them

## Debug code

- No debug statements in committed code: no `print()`, `console.log()`,
  `fmt.Println()`, or equivalent used for debugging
- No hardcoded breakpoints (`debugger`, `pdb.set_trace()`) in committed code
- No commented-out code blocks — delete dead code; version control is the
  history
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
- A throwaway probe also fits a uniform mechanical migration: when one
  edit repeats across hundreds of identical call sites (e.g. inserting a
  new required field at a fixed anchor in a large data file), a small
  `probe_*` script that performs the insertion is faster and safer than
  hand-editing or an opaque `sed` one-liner. The diff is the audit trail,
  not the script — review the diff, then delete the probe before the
  commit

## Automated enforcement

- Quality conventions in this document are enforced automatically via
  quality gates (editor → pre-commit → CI)
- A code or data generator MUST emit output that passes the project's
  linters and formatters natively — never rely on `lint --fix` as a
  post-process step. A fix pass at the consumer end hides the generator's
  responsibility, makes every re-emit a noisy diff, and confuses
  contributors who regenerate and see unexplained changes. Any time
  `lint --fix` is needed to clean generated output, treat it as a
  generator bug to fix at the source

## Testing

- Tests must pass before merging to `main`
