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

## Revisit triggers

[ID: quality-revisit-trigger]

A revisit trigger names the condition that reopens a deferral. Nothing
polls it, and the record holding it is not re-read on a schedule, so by
default it fires into an empty room: a record describing a constraint
that has since lifted reads exactly like a live one.

- The obligation attaches to the action, not to the record. An actor
  who takes a step that fires a recorded trigger MUST reopen the
  decision in the same change — as a superseding record, or as a ticket
  carrying the evidence that the trigger fired
- Before changing a piece of project state, search the records for
  triggers naming it. The actor usually does not know that a record
  names their action, and the search is the only thing that connects
  them. Write triggers in a consistent, greppable form for exactly that
  reason — a trigger nobody can find is a trigger nobody watches
- State what would detect the trigger: a scheduled check, a gate that
  fails, or the surface a reader would notice it on. Where nothing
  would, record that detection is a person looking, so the cost is
  visible rather than assumed away. A trigger that fires outside this
  repository has no automatic watcher at all
- A trigger is a claim about the world and decays like any other.
  Re-verify it against the system rather than by re-reading the record,
  and state that check beside the condition, so re-verifying costs one
  command rather than a re-derivation

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
- Cognitive complexity ≤ 15 per function — enforced by static analysis;
  each nesting level and decision point increases the score. The tool is
  bound per ecosystem in `base-<language>-tooling`, not here

- Maximum nesting depth of three levels — use early returns and guard clauses
  to reduce indentation rather than adding else branches
- No boolean flag parameters — they force the caller to read the implementation
  to understand what `true` means; use an enum or two named functions instead
- Name a pluggable tier for what it requires of the caller, not for the
  library behind it — a public enum member, CLI flag, or result
  discriminator MUST be named for the capability or requirement it
  represents; a private symbol MAY name the library it drives. Prefer
  `Transport.HTTP` / `JS` / `HEADED` over `Transport.PLAYWRIGHT` /
  `NODRIVER`: the first says when to pick each, the second makes the
  caller learn what each library is
- Corollary: if swapping the implementation would force a caller to
  change code, the name has leaked. Which library sits behind a tier
  changes without notice and is not the caller's problem
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
- When retiring a concept — a label, a lane, a flag, a convention — sweep
  every surface that still instructs its use, not just the source tree. An
  open ticket body, a planning document, or a draft change description is a
  delayed write: implemented verbatim later, it reintroduces the concept
  into the very files the retirement stripped it from. The sweep is done
  when a search for the concept returns only historical records — decision
  logs, change logs, journals — and no surviving instruction to apply it
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
- **Split an oversized module into a package behind its import path**:
  when `mod.py` becomes `mod/`, preserve the public import path via
  `__init__` re-exports so callers and the test module are NOT modified.
  The unchanged suite is then the split's regression oracle; rewriting
  the tests' imports to the new submodules forfeits it, by touching the
  oracle in the same change that restructures the code under test. This
  is the in-repo step toward **Build extraction-ready internal
  modules** — the same `__init__`-owns-the-API discipline, applied
  before extraction is on the table
- Split by a cohesive seam (data-flow stage is the usual one) and keep
  the submodule graph acyclic: each submodule imports only earlier
  stages, and no submodule imports the package `__init__`. Re-export
  the public API and the private helpers the test module imports
  directly, listing both in `__all__` so the linter does not flag them
  unused. Constants travel with the functions that use them — a central
  `constants.py` orphans provenance from the code and fights cohesion
- Verify a split with the cheap static gates before the slow suite:
  linter undefined-name/unused, an import smoke check, then test
  collection. They catch every mechanical split error instantly, so the
  full suite runs once — and a green run of the untouched suite plus a
  byte-identical output diff is what proves the split behaviour-neutral

## A workaround comment is a half-filed defect report

[ID: quality-rejected-mechanism-sweep]

A comment explaining why one module avoids a construct is evidence that
the construct is wrong everywhere, not a note about local taste. Someone
diagnosed a shared mistake, fixed the module they were looking at, and
had no reason to check the others — so the siblings that still use it
carry no comment saying so, and this comment is the only record that
they were never checked.

- When a comment names a **rejected mechanism** — a specific construct,
  call, or idiom recorded as not working — grep the codebase for that
  mechanism before moving on: `grep -rn '<the construct>' <source root>`.
  The pattern is already written down for you, in the comment. Scope the
  search to the construct, not to the prose around it
- Read every hit as a suspected instance of the same defect rather than
  as a style question. The comment recorded an outcome, and the outcome
  does not depend on which module the construct sits in
- Where the sweep finds none, the comment is doing its narrower job and
  the cost was one command. Where it finds hits, what looked like a
  design note was an unfixed bug with a known diagnosis
- This is the discovery half of `testing-shared-path-breadth`, which
  covers verifying every call site once they are known. The sweep is how
  the other call sites are found at all — from a comment rather than
  from a diff

## Destructive operations

[ID: quality-destructive-ownership]

An operation that deletes, truncates, overwrites or kills decides what
to act on from its inputs, and the inputs are precisely what fail. A
configurable path resolves somewhere unintended when the value is empty
or the variable unset; a before-and-after sample attributes a process
that merely appeared during the window. Either failure alone is
survivable. Paired with a filter on a generic property — a file
extension, a process name — it destroys something the user never
offered the operation.

- A destructive operation acts only on what it can prove it created.
  Proof is a property the operation's own subsystem wrote: process
  ancestry, a key scheme, a filename prefix, a marker file, an ownership
  tag. Never a path, a configuration value, or a file extension
- Where the proof is unavailable the operation finds nothing — not an
  error, not a prompt, not a best guess. The safe outcome of a lost
  ownership check is that the destructive step has no work to do, so a
  mis-resolved target yields an empty sweep rather than a broad one
- Validating the input is not a substitute. A wrong path can be
  perfectly valid, so the two defences fail independently and both are
  needed: reject the empty configuration value, and match the key scheme
- The rule holds beyond caches — a build tool clearing an output
  directory, a log rotator pruning old logs, a temp-file reaper. Anywhere
  the target set is "the files in a directory someone configured"

The ownership filter looks redundant, and that is the whole point.
Inside the directory it was written for it matches everything the
generic pattern matches, so the next reader to call it dead code will be
right about the common case and wrong about the reason it exists:

```
match on ".html"              wrong directory -> README.html deleted
match on "[0-9a-f]{16}.html"  wrong directory -> nothing matched
```

The path bug still happens. It stops being destructive.

## Expensive computations (if applicable)

[ID: quality-expensive-compute]

A step built on an iterative numerical routine (a fixed-point solver, an
optimizer) or on a memory-heavy intermediate fails in ways that produce a
plausible answer rather than an error. These rules keep the failure loud
and the cost paid once.

### Verify convergence — escalate, then fail loud

- A routine that exposes a convergence flag but does not force the caller
  to read it MUST be wrapped in one helper that checks the flag. An
  unconverged result handed back as if it were valid feeds a wrong number
  straight downstream
- On failure, escalate through progressively stronger and slower
  stabilization strategies, cheapest first, before raising a descriptive
  error naming what would not converge. The ladder fires ONLY on
  non-convergence, so the path that already converges is untouched
- Keep the ladder unit-testable without the heavy engine: each
  stabilization step is a small function, the driver is pure
  orchestration, and a stub with scripted per-attempt convergence
  exercises every rung

### An output-changing approximation is opt-in and off by default

- A speed knob that shifts the numbers (a lower-rank approximation, a
  coarser grid) MUST default off, so the canonical output is never
  silently perturbed
- Carry it as a per-run field in the same single source of truth as the
  rest of the run's parameters, so a run that needs it is self-reproducing

### Size the budget to the box; spill or refuse, never OOM

- A memory-heavy step detects its real budget (env override → container
  cgroup limit → physical RAM, scaled for headroom) rather than assuming
  a fixed library default
- Estimate the large intermediate up front: keep it in RAM while it fits,
  stream it to a disk scratch path beyond that, refuse past a hard
  ceiling. A diagnosable error beats an OOM crash
- The scratch path MUST be real disk, not a RAM-backed tmpfs

### Persist the reusable intermediate, not just the scalar read off it

- When already paying for an expensive computation, persist its reusable
  internal state to a checkpoint, not only the scalar this caller needed.
  Discard the state and the next question about the same input forces a
  full re-run
- Make it opt-in (a checkpoint-path parameter, default off) so cheap
  callers pay nothing, and store the checkpoint with the other
  regenerable artifacts (gitignored)
- Validate the round-trip once on a small case before trusting a long
  batch to it — including any wrapper or proxy layer around the engine,
  which can silently swallow the checkpoint parameter

## Calibration discipline

[ID: quality-calibration]

When a tool is calibrated against reference data (test fixtures with
known-correct outputs, benchmark expected results, eval data, decision
thresholds), the calibration is silently invalidated by suspect ground
truth, by a threshold tuned to mask a broken measurement, and by
reference values produced by the same actor that runs the tool. The
rules below govern that, and what a calibrated pipeline may then emit:
a value it cannot justify is worse than a gap.

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

### Report a derived quantity only where it is well-defined

Distinct from the absence rules above, which cover a source that carries
no value. Here the value is computable and the arithmetic succeeds — the
condition that gives the result meaning is what fails.

- A derived quantity is often well-defined only under a condition (a
  non-zero denominator, a minimum sample size, a non-degenerate input).
  Report it only where that condition holds
- Where it does not hold, leave the cell empty — not zero, not a
  placeholder, not the condition-violating value. An empty cell states
  "undefined here"; a number computed outside its domain is
  indistinguishable from a measurement and pollutes every downstream
  aggregation
- The check belongs at the point of emission. A consumer cannot recover
  the condition from the value alone, which is exactly why the artifact
  must not carry it

### A user-visible artifact takes its bar from the strictest consumer

- When a derived or extracted artifact feeds several consumers of
  differing strictness AND is itself user-facing (rendered or displayed,
  not only an internal input), its acceptance bar is set by the strictest
  **visible** consumer
- Do NOT loosen it to match a coarser downstream consumer, and do NOT
  lower it for throughput. Coarsening the acceptance metric to a bucketed
  score, or dropping a label only the visible artifact reads, is correct
  for the score and corrupts the table a user looks at
- The compatible throughput lever is honest gaps, not a looser bar: an
  ambiguous cell is blanked per the rule above, never emitted wrong

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

### A detector's precision is not its cost

- A false-positive rate says how often the verdict is wrong and nothing
  about what a wrong verdict destroys. A heuristic that gates an
  expensive fallback MUST be evaluated on both, because a detector with
  an excellent rate can still be unshippable
- Ask first whether a positive verdict discards the cheap result or
  holds it. Where the cheap tier returns a sentinel instead of its body,
  the result is destroyed at the moment the heuristic fires, and the
  fallback's availability becomes part of the heuristic's correctness
  rather than an operational detail
- Ask what the system returns when the fallback cannot run — an optional
  dependency absent from a default install is the common deployment, not
  the rare one. Where the answer is "nothing", the heuristic's failure
  mode is data loss, and that is not the precision bar of a heuristic
  which merely costs time
- Prefer preserving the cheap result, so an unavailable fallback
  degrades to a result plus a warning rather than to nothing. That is
  also what returns the question to one about latency, where the
  false-positive rate is the right measure
- No amount of tuning finds this. It is a property of the surrounding
  control flow, and it can invert a decision that looked like a
  threshold problem

### A spike reports the corpus it did not have

- A spike that cannot clear its own evidentiary bar with the available
  data records the corpus gap as its finding, rather than lowering the
  bar to produce a shippable answer
- A rule that survives every case in a set the rule's own author wrote
  is fitted to that set, not measured against it. Count the cases that
  were captured independently of the rule; that count is the evidence,
  and the rest is illustration
- "The evidence does not exist yet, and here is exactly what would have
  to be captured" is a deliverable. State that it is one, because it
  reads as a non-answer otherwise

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

- Encode every committed file in UTF-8
- Identifiers MUST be ASCII. A name is typed, searched and compared,
  so a character unreachable from a keyboard or confusable with the
  ASCII it resembles turns all three into guesswork — a Cyrillic `а`
  in a variable name reads as Latin `a` and matches nothing. The
  check is language-specific, because only a tokenizer can tell an
  identifier from the prose around it. The Python one, which prints
  nothing when clean:

  ```bash
  py - <<'EOF'
import io, subprocess, token, tokenize

# Identifiers only. Comments, docstrings and string content are
# documentation and carry no charset restriction.
tracked = subprocess.run(["git", "ls-files", "*.py"], capture_output=True,
                         text=True).stdout.split()
for name in tracked:
    with io.open(name, "rb") as handle:
        for item in tokenize.tokenize(handle.readline):
            if item.type != token.NAME:
                continue
            bad = sorted({ord(c) for c in item.string if ord(c) > 127})
            if bad:
                codes = " ".join("U+%04X" % c for c in bad)
                print("%s:%d %s %s" % (name, item.start[0], item.string, codes))
  EOF
  ```

- Comments, docstrings and string content carry NO charset
  restriction, and neither does documentation. They are written for
  readers, in whatever language and symbols the reader needs. A rule
  that reaches them buys a house typography at the cost of everything
  else, and it reaches further than it looks: a generator whose string
  literals draw a diagram is writing a document, not code
- A program that writes text MUST set its output encoding explicitly
  rather than inheriting the console's. Inheriting is what turns a
  correct string into mojibake on someone else's machine, and the
  boundary is what needs fixing, not every string that crosses it. In
  Python: `sys.stdout.reconfigure(encoding="utf-8")` at the entry
  point
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
- In code comments, docstrings and commented configuration, go further:
  never cite a ticket, PR, or ADR *number* at all — code outlives the
  tracker, so state the substance instead (name the descriptor, source,
  or derivation, not "see #123" or "per ADR 0002"). Markdown docs
  (README, ADRs, the dev journal) are the opposite: cross-referencing
  issues and ADRs by number is their job. One exception in code:
  non-obvious or scientific logic MAY name a *source* (author + year +
  method — "Rappé 1992"), which ages gracefully where an issue number
  does not. Enforce with a test that greps comments, docstrings and
  commented configuration for `#\d+` / `ADR\s*\d+`
- A block comment MUST sit directly above the item it documents: never
  trailing to the right of code (tool directives like `# noqa` / `# nosec`
  are excepted), and never separated from that item by a blank line
- Separate each comment-plus-item group from the next with a single blank
  line, so the comment and the lines it explains read as one unit
- A comment that is the first thing inside a block or a bracketed literal
  is exempt from that separation: it opens the first group rather than
  dividing two, and the line above it is the `def`, `if`, `for`, `try` or
  opening bracket the comment is inside. There is nothing to separate it
  from, and a blank line inserted there detaches the comment from the item
  it documents — the violation the rule above forbids
- Wrap comment prose to the project's configured line-length limit, the same
  limit as code. Enforce this for commented configuration files
  (`pyproject.toml`, YAML, CI workflows) too, even where the linter does not
  scan them
- Check — comment layout, for the two violations that are mechanically
  visible: a comment block with code directly above it and no blank line
  between them, and an aside to the right of code that is not a tool
  directive. Scope: Python sources, read through `tokenize` — a line-based
  grep reports the `#` in a usage example inside a docstring, which is not
  a comment at all. `OPENERS` carries the exemption above; test it against
  the code the line above *ends* with, since a line closing the previous
  entry (`],`) opens nothing and its comment is a real finding. Whether a
  comment sits above the *right* item is not mechanical and stays
  declarative; wrap width is the formatter's. Pass condition: the command
  reports how many files it checked and prints nothing after that:

  ```bash
  py - <<'EOF'
import io, pathlib, tokenize
DIRECTIVES = ("noqa", "nosec", "type:", "pragma:", "pylint:", "fmt:", "mypy:")
SKIP = (".venv", "venv", "build", "dist", ".git", ".tox")
OPENERS = (":", "(", "[", "{")
paths = [p for p in sorted(pathlib.Path(".").rglob("*.py"))
         if not any(part in SKIP for part in p.parts)]
print("Python files checked: %d" % len(paths))
for path in paths:
    src = path.read_text(encoding="utf-8").splitlines()
    with io.open(str(path), "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type != tokenize.COMMENT:
                continue
            row, col = tok.start
            if src[row - 1][:col].strip():
                if not tok.string.lstrip("#").strip().startswith(DIRECTIVES):
                    print("%s:%d: aside to the right of code"
                          % (path.as_posix(), row))
            elif row > 1 and src[row - 2].strip():
                above = src[row - 2].split("#")[0].rstrip()
                if not src[row - 2].strip().startswith("#") and not (
                        above.endswith(OPENERS)):
                    print("%s:%d: comment block with code directly above it"
                          % (path.as_posix(), row))
  EOF
  ```

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

### The scripts directory

A probe never lands, so `scripts/` is not where throwaway work lives — a
directory cannot be the home for files that must not be committed. What it
holds is maintained tooling that is not shipped: unshipped is a packaging
fact, not a licence to leave a file unowned.

- A file under `scripts/` MUST be eligible on one of three grounds:
  invoked by a command the documentation names, executed by CI, or
  imported by a file that is. The third is a real branch and not a
  courtesy — a helper module nothing invokes directly is still live, and
  a rule with only the first two deletes it
- A file eligible on none of the three MUST be deleted rather than
  reshaped. Its findings, if any, were supposed to have moved into source
  comments, a decision record or the docs when the change that used them
  landed
- Where the project keeps a persistent `scripts/`, every file in it is
  covered by the same review and formatting rules as shipped source. A
  directory exempt from them accumulates files nobody will open

No automated gate reaches these files on its own. An unshipped script is
outside the packaged artifact, so the packaging checks say nothing; it
carries no tests, so coverage says nothing; and where a project froze lint
findings per file on adoption, it sits inside the freeze and the linter
says nothing either. That combination is why the directory accumulates,
and why this rule needs a check rather than a convention:

```bash
py - <<'EOF'
import pathlib, subprocess

SCRIPTS = pathlib.Path("scripts")
files = sorted(p for p in SCRIPTS.rglob("*")
               if p.is_file() and p.suffix in (".py", ".sh", ".ts", ".js"))
print("scripts inspected: %d" % len(files))
if not files:
    print("no scripts directory, or it holds none - nothing to check")
    raise SystemExit(0)

tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
corpus = []
for name in tracked:
    if name.startswith("scripts/"):
        continue
    try:
        corpus.append(pathlib.Path(name).read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        pass
print("files searched for a reference: %d" % len(corpus))
blob = chr(10).join(corpus)

dead = [f.as_posix() for f in files if f.as_posix() not in blob and f.name not in blob]
print("unreferenced: %d" % len(dead))
for name in dead:
    print("  %s" % name)
EOF
```

Pass condition: the check prints how many scripts it inspected and how many
files it searched for a reference, then `unreferenced: 0`. Both counts are
load-bearing — a searched count of zero means the corpus never loaded, and
reports the same clean result as a directory where everything is
referenced. A name appearing anywhere in the corpus counts, which
deliberately under-reports: it flags only a file nothing mentions at all,
so every hit is a real finding rather than a judgement call.

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
