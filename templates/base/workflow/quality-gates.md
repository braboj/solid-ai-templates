# Base — Quality Gates

[ID: base-quality-gates]
[DEPENDS ON: templates/base/core/quality.md, templates/base/core/git.md, templates/base/core/testing.md, templates/base/core/config.md]

Stack-agnostic quality gate model. Defines the layers, categories,
thresholds, and constraints. Stack templates extend with concrete tools.
Platform templates extend with CI-specific integration.

---

## Shift-left principle

[ID: quality-gates-principle]

The earlier a defect is caught, the cheaper it is to fix. Every check
that can run locally MUST run locally. CI is the backstop, not the first
line of defense.

```
Editor (0s) → Pre-commit (1-5s) → CI (1-5min) → Code review (hours)
```

---

## Three-layer gate model

[ID: quality-gates-layers]

### Layer 1 — Editor (instant feedback)

Runs in the developer's IDE as they type. Zero friction.

- Every project MUST provide config files that enable checks automatically
  when the project is opened in a supported editor
- Checks: lint, format, type check
- The editor's type-checker MUST defer to the CI type gate — one
  type-checker at one strictness, never two. A bundled editor checker
  runs its own stricter analysis by default and floods the editor with
  diagnostics the CI gate is configured to ignore, so contributors chase
  false positives and "green in CI" stops meaning "green in the editor"
- Turn the bundled checker's type evaluation off, and surface the CI
  checker's own diagnostics live through its editor extension instead.
  Only the diagnostics layer defers — completion, hover and rename are
  unaffected
- The editor config that mirrors CI MUST be tracked, not left to each
  contributor to reproduce

### Layer 2 — Pre-commit hooks (1–5 seconds)

Runs automatically before every commit. Blocks bad commits locally.

- Every project MUST have pre-commit hooks
- The hook framework is stack-specific (see stack template)
- Checks: lint, format, type check, secret detection, file hygiene
  (trailing whitespace, merge conflict markers, large files)

### Layer 3 — CI (1–5 minutes)

Runs on every PR. The final gate before merge.

- Every project MUST have a CI workflow that runs on PRs
- CI checks MUST be configured as required status checks in branch
  protection — a passing CI run that does not block merge is
  informational, not a gate
- The protection MUST bind administrators. The administrator exemption
  is off by default and easy to leave off, and it satisfies the
  required-checks rule while leaving a red pull request mergeable. On a
  single-maintainer repository the exempt administrator is the only
  person the gate would ever apply to, and the configuration passes any
  audit that reads the required-checks list
- Where the member count is below the required approving-review count,
  that requirement blocks every merge rather than gating it, since
  nobody can approve their own pull request. Set the count to zero and
  rely on administrator enforcement. The two settings look
  interchangeable and are not: the review count governs who reviews,
  the protection scope governs whom the gate binds
- CI MUST duplicate Layer 2 checks — pre-commit hooks can be bypassed
  with `--no-verify`
- CI adds checks that cannot run locally: deep security analysis (SAST),
  test suite, coverage measurement, build verification
- The CI platform is project-specific (see platform template)

---

## Gate categories

[ID: quality-gates-categories]

Every project MUST enforce checks in the following categories. Stack
templates map each category to a concrete tool.

| Category         | Layer 1 | Layer 2 | Layer 3 | Description                                          |
| ---------------- | ------- | ------- | ------- | ---------------------------------------------------- |
| Lint             | MUST    | MUST    | MUST    | Code smells, unused variables, complexity            |
| Format           | MUST    | MUST    | MUST    | Consistent style (indentation, spacing, line length) |
| Type check       | SHOULD  | SHOULD  | MUST    | Type errors before runtime                           |
| Secret detection | —       | MUST    | MUST    | API keys, tokens, passwords                          |
| File hygiene     | —       | MUST    | —       | Trailing whitespace, merge conflicts, large files    |
| Security (SAST)  | —       | —       | MUST    | Static analysis for vulnerabilities                  |
| Tests            | —       | —       | MUST    | Unit and integration tests                           |
| Coverage         | —       | —       | MUST    | Percentage of code exercised by tests                |
| Build            | —       | —       | MUST    | Does it compile / build successfully                 |

Stack templates MAY add additional categories (e.g. link checking, site
quality scoring for web projects, docstring enforcement for Python).

### A named tool that cannot run is declined, not left blank

Stack templates name tool pairs for a category — a local scanner plus a
hosted analysis service is the usual shape. Sometimes only one half is
reachable: the hosted half needs a paid tier the repository does not have,
a plan the organisation has not bought, or a visibility setting the project
deliberately does not want.

- A gate category naming more than one tool is satisfied by the tools that
  can run, plus a recorded decline for each that cannot
- The decline MUST name why the tool is unavailable and the concrete
  condition that would reopen it, and MUST live in a decision record rather
  than a comment. This is the YAGNI revisit trigger from `base-quality`
  applied to tooling: a deferral without a trigger gets re-argued or
  quietly forgotten
- A category MUST NOT be left blank because one named tool is unavailable.
  It then reads as unimplemented, the next audit re-raises it as a gap, and
  someone re-derives the same unavailability from scratch
- A workflow for a tool that cannot run MUST NOT be committed to fill the
  row. It sits permanently red or permanently skipped, which is the
  gate-by-omission shape `quality-gates-scope-agreement` names

This governs what a compliant implementation looks like when a named tool
is genuinely unreachable. It relaxes no category from MUST.

### Lint-rule bumps: fix the source on its own PR first

When a dependency bump adds a lint rule that flags existing source:

- Write the fix in the older rule's API (usually forward-compatible)
  on its own branch, and merge that fix-PR to `main` first
- Then `@dependabot rebase` the bump PR so it lands clean on green
- Do NOT push the fix onto Dependabot's branch — keep the bump as
  Dependabot's own commit so it stays recreatable on future runs

---

## Thresholds

[ID: quality-gates-thresholds]

| Metric                   | Threshold | Enforcement                  |
| ------------------------ | --------- | ---------------------------- |
| Lint errors              | 0         | CI fails                     |
| Format compliance        | 100%      | CI fails                     |
| Type errors              | 0         | CI fails                     |
| Security (high/critical) | 0         | CI fails                     |
| Secrets detected         | 0         | Pre-commit blocks + CI fails |
| Build                    | Success   | CI fails                     |

### Coverage policy

- **New projects** — 80% from day one; CI fails below threshold
- **Legacy projects** — coverage reported as warning only; CI shows the
  number but never blocks; flip to error when the team has the mandate
  to invest in testing
- **Un-runnable code** — omit modules that genuinely cannot execute in
  CI (native extensions, GPU paths, container-only code with no wheels
  on the runner) from the coverage denominator, and validate them
  out-of-band (a separate suite, integration environment, or tracked
  artifacts). Scoping the denominator keeps the gate honest at 80%
  instead of dropping the bar to a meaningless number that lets
  permanently-un-runnable code drag the percentage down as dead weight
- **Omit-list is a contract** — a new pure module is in scope by
  default and MUST be tested; adding a module to the omit-list is a
  reviewable decision, never a silent escape. This is the coverage
  analogue of the complexity ratchet (see `quality-gates-complexity`):
  make a partial codebase's gate honest without lowering the bar

Stack templates MAY add additional thresholds (e.g. Lighthouse scores).

---

## Complexity gates

[ID: quality-gates-complexity]

- Complexity gates SHOULD measure cognitive complexity (nesting plus
  control-flow interruptions) rather than only McCabe branch counts.
  The two metrics genuinely disagree in practice: McCabe flags flat,
  linear section emitters while passing deeply nested logic — the
  opposite of what a readability standard is after
- The gate MUST name a tool, and the language layer is where it is
  named. A category whose tool is chosen per ecosystem does not belong
  to this file; `base-<language>-tooling` binds it
- Where a language's lint tool has no cognitive-complexity rule, the
  gate needs a second tool rather than a waiver. Stating the gate
  without one leaves a SHOULD nothing can satisfy
- Retrofit onto an existing codebase via a ratchet: commit a baseline
  that freezes current offenders at their recorded values; CI fails
  only when an over-threshold function is new or has increased. The
  gate turns on from day one with zero up-front refactoring, and the
  baseline doubles as a measured refactor priority list
- Pin the tool version when the baseline file format is
  version-sensitive

---

## Mutation testing, where the suite is mature enough to earn it

[ID: quality-gates-mutation]

The coverage gate answers how much code a run exercised. It cannot answer
whether the assertions hold anything down, and a suite can sit at eighty
per cent coverage with toothless assertions while coverage reports the
same number either way. Mutation testing injects small faults and asks
whether the suite notices, which measures the tests rather than their
reach. That matters most where merges ride on green CI, because there the
gate is only as strong as the tests behind it.

- Mutation testing is OPT-IN. It reruns the suite once per mutant, so its
  cost is suite runtime times mutant count, and it buys least on an
  immature suite where nearly everything survives and the report is a
  backlog rather than a signal
- Adopt it where the suite is already mature and the code is
  consequential — a parser, a permission check, a money path — rather
  than across the whole tree
- The score MUST be introduced as a baseline with a ratchet, never as a
  hard cliff. A first run on real code lands far below any figure worth
  publishing, so a cliff set there is unreachable and a cliff set below
  it is meaningless. Record the measured score and require that it not
  fall, the way `quality-gates-retrofit-ratchet` freezes instances
- Say which scope produced any score recorded. A diff-scoped
  pull-request run and a whole-module audit answer different questions,
  and a figure with no scope attached is read as a baseline by whoever
  finds it next
- A surviving mutant is a question, not a defect. Some mutants are
  semantically equivalent to the original and cannot be killed, so the
  project MUST be able to record one as accepted with its reason.
  Without that, the ratchet is a gate nobody can satisfy and the first
  equivalent mutant retires it

---

## Retrofit a gate by freezing instances, never by narrowing it

[ID: quality-gates-retrofit-ratchet]

`quality-gates-complexity` gives the ratchet for one metric. It generalises,
and it has a look-alike that is far more tempting because it is smaller:
writing a baseline is work, deleting a field from a comparison is one line
and the diff reads as a simplification. Both turn a red gate green. Only
one leaves a gate behind.

- A red gate MAY be made green by exempting the failing instances. It MUST
  NOT be made green by narrowing what the gate evaluates. Ratcheting freezes
  which instances fail and leaves the analysis intact; removing a field from
  a comparison, disabling a strict sub-flag or loosening a matcher removes
  the analysis for every case, including ones nobody has written yet
- The tell is what the exemption costs to reverse. A baseline entry is
  deleted and the case is checked again. A narrowed comparison leaves no
  record that the property was ever checked, so nothing prompts anyone to
  restore it
- When the failing case is a genuine defect and the fix is small, fix it. A
  check narrowed to accommodate one known defect is a permanent price paid
  for a temporary problem

### Retrofitting a linter

Adopting a modern linter on an existing codebase produces a finding count
that makes the gate unadoptable as written. Three responses, two of which
are traps:

| Response | Outcome |
|----------|---------|
| Fix everything first | Buries the gate change under a mechanical diff no reviewer can separate from a behavioural one, and gates untouched code the change was never about |
| Ignore the offending rule families globally | Never ends. New code is ungated on exactly the rules the project says it wants, nothing ever fails, so nothing is ever fixed |
| Freeze per file | Works |

- Enable the full rule selection, then record the violations existing on
  adoption day in a per-file ignore table, each file listed with exactly the
  rules it broke. A new file has no entry and is gated on everything, an
  existing file cannot get worse, and shrinking the table is the migration
- The table MUST be generated from the linter's own output, never curated by
  hand. A hand-maintained table drifts and becomes a place to hide findings
- The linter MUST be pinned to a minor range. The table records one
  version's findings, so a release adding rules to an already-selected
  family fails the gate on untouched code — the same reason
  `quality-gates-complexity` pins when the baseline format is
  version-sensitive
- A file MUST NOT be added to the table to make a gate pass, and an existing
  entry MUST NOT be widened. Without that rule the table becomes the global
  ignore list this whole approach exists to avoid

State the known cost rather than discovering it later: a file-level freeze
does not newly gate an existing file when it is edited. Line-level would,
and no widely available linter offers it.

---

## Editing a test moves the standard, not the work

[ID: quality-gates-test-edit-boundary]

`quality-gates-retrofit-ratchet` bans turning a red gate green by narrowing
what it evaluates. Where the tests are the source of truth for correctness,
the same move is available one level up, and a merge-on-green policy does
not see it: the tests are both the standard and a set of files the change
may edit. A suite that was weakened still reports green, and that green
proves only that the code matches whatever the tests were reduced to — not
that the behaviour they guarded still works.

The boundary is between proposing work and redefining the standard the work
is measured against. Strengthening the specification needs no ceremony;
weakening it is a different act and takes a person.

- A change MAY strengthen the specification without escalation. Adding a
  test, or tightening an assertion, can only narrow what passes, so a green
  run afterwards means more than it did before
- A change that deletes, loosens or rewrites an existing test MUST state
  why, and MUST NOT merge on a green suite alone. It changes what correct
  means, and the suite cannot report that it has
- Where merges ride on green CI, separate the two mechanically: a diff
  touching an existing test file loses auto-merge or lenient-review
  eligibility, and a diff that only adds test files keeps it. The filter is
  the enforceable half; the stated reason is the half a reviewer reads
- Put the invariants that must not be renegotiated under code ownership —
  safety, authentication, authorisation — so weakening one needs the owner
  rather than the author

Classify a change against the project's test root, reporting what it
inspected as well as what it found:

```bash
git diff --name-status origin/main...HEAD -- 'tests/*' | wc -l
git diff --name-status origin/main...HEAD -- 'tests/*' | grep -vE '^A'
```

The first line counts the test-file changes inspected. The second lists
every one that is not a pure addition, and MUST be empty for a change to
keep the lenient path. Unlike a coverage scan, a zero here is a real
answer and not a broken path — it means the change touched no tests at
all, which needs no escalation.

This is governance, not a new pass/fail metric: it adds no threshold and
changes nothing about which gates run.

---

## Skip noisy gates when input is unchanged

[ID: quality-gates-skip-equivalent]

Some gates measure a property of the *build output* (Lighthouse
score, bundle size, visual diff, e2e behavior) and have enough
single-sample variance to produce false positives near their
threshold. When a PR's file set cannot affect the gate's input —
e.g. a Dependabot bump of `package.json` + `package-lock.json` for
a static site — running the gate is pure noise. Failure on a
byte-identical build output is not a real regression; it is
runner-variance pretending to be one.

For a gate to be a skip candidate it MUST satisfy all three:

1. **Output-measuring** — the gate evaluates the build output, not
   the source (Lighthouse, bundle-size, visual diff, e2e, screenshot
   diff)
2. **Noisy at sample size 1** — single runs near the threshold
   produce different verdicts on retry without any code change
3. **Path-determined input** — there is a file-pattern subset that
   provably cannot change the build output (lockfile-only changes
   on a static site, README changes, etc.)

Deterministic gates (lint, type check, unit tests, build success)
and gates whose input depends on more than file changes (anything
that hits the network or external state) MUST NOT be skipped.

Example with GitHub Actions `dorny/paths-filter`: skip the
Lighthouse job when the PR touches only dependency manifests
(`build` still runs to verify the bump compiles):

```yaml
- uses: dorny/paths-filter@v3
  id: changes
  with:
    filters: |
      output_affecting:
        - '!package.json'
        - '!package-lock.json'

- name: Lighthouse
  if: steps.changes.outputs.output_affecting == 'true'
  run: npm run lighthouse
```

Document the skip rule in an ADR alongside the workflow change —
the reasoning ("this gate cannot produce signal on these PRs")
should be discoverable later when someone wonders why the gate
sometimes doesn't run.

---

## Reading a gate verdict honestly

[ID: quality-gates-verdict-reading]

A gate verdict is a signal to interpret, not a conclusion to act on
blindly. Two failure modes sit on either side of the pass/fail line.

### Disaggregate verdict, plausibility, and accuracy

When a gate fires, its single verdict often conflates three judgments:

- **Verdict** — what the gate says (pass / fail / LOW)
- **Plausibility** — is the output *shape* consistent with priors,
  sanity checks, and schema invariants?
- **Accuracy** — does the output match ground truth where it exists?

A "LOW" can mean the output is inaccurate, the plausibility check is
unsound for this input class, or both — and each implies a different
fix (fix the producer / tune the check per-class / both). Separate them
before acting. Worked example: a gate's plausibility check flagged a
record whose output matched the reference on nearly every field — the
check's assumption was unsound for that input class, so the fix was a
per-class exception to the check, not a change to the producer. The
verdict alone pointed the wrong way.

### Lenient gates need a human residual check

The complement to a noisy gate is a lenient one: it passes, but a human
glance catches a defect the gate cannot. A single-sample dip in a curve
can pass a tolerance averaged across samples. Tightening the threshold
to catch it would mis-flag legitimate runs; instead keep the gate AND
document that the artifact type requires a maintainer-eye review before
commit. A passing gate is necessary, not sufficient.

---

## Gate scope agreement

[ID: quality-gates-scope-agreement]

In a polyglot repo where a secondary toolchain lives in a subdirectory
(e.g. a Python `tools/` directory inside a TypeScript static site), or
where captured test fixtures (scraped HTML/JSON representing real
external byte sequences) live in-tree, three failure modes silently
break the gate: the formatter walks files it should not touch, the
PR gate skips work the deploy gate runs unconditionally, and an
aggregated `gate` job reports success on skipped checks. The rules
below close those gaps.

### Ignore lists and CI path-filter MUST agree

- The formatter/linter ignore lists and the CI path-filter that
  triggers the gate MUST cover the same set of paths — a directory
  excluded from one MUST be excluded from the other
- A secondary toolchain with its own test runner is verified by that
  runner, not the primary stack's gate. Document the split in an ADR
- Captured test fixtures (scraped HTML/JSON representing real external
  byte sequences) MUST be excluded from the formatter — they must
  stay byte-for-byte, and reformatting them changes the test input

### Formatter-vs-generator escalation

When a generator (script, codegen, scaffolder) emits a file into a
directory that a commit-time formatter (prettier, black, gofmt) walks,
three things MUST hold together:

- The emitted path MUST appear in the formatter's ignore list
  (`.prettierignore`, black `force-exclude`, or equivalent)
- A CI staleness gate (`<generator> --check`) MUST run on the same
  paths (see `quality-gates-staleness`)
- Both MUST land in the same PR — the ignore line without the gate,
  or the gate without the ignore line, leaves silent drift

Without all three, the formatter mutates generator output between
commits and the generator's `--check` fails on a clean checkout — so
the staleness gate cannot even be wired into CI.

### Skipped is not passed

- When a code-touching change would skip the build job via a
  path-filter, the aggregation / `gate` job MUST NOT report success
  by default
- Distinguish "skipped because out of scope" from "skipped
  erroneously" — the former is a pass equivalent, the latter is a
  gap. An aggregator that treats them identically is the
  gate-by-omission anti-pattern
- A passing-because-skipped check looks identical to a passing
  check in the GitHub UI; the difference MUST be encoded in the
  workflow, not left to reviewer attention
- That encoding MUST be verified on the skipped path, not only on the
  failing one. A failed upstream trips a correct fan-in (comparing
  every result against success) and a naive one (comparing against
  failure) alike, so only a skipped upstream separates them. Make one
  upstream job skip temporarily, confirm the gate fails, and revert —
  the whole test is one commit and one revert

### A configured scope is verified by coverage, not exit status

A gate that ran, went green, and covered almost nothing renders
identically to a real pass. It is worse than a skip, because a skip is at
least visible as one. The check and the parameter setting its input scope
are separate things, and review usually looks only at the check:

| Gate | Scope parameter | Collapsed scope still exits zero |
|------|-----------------|----------------------------------|
| History secret scan | checkout fetch depth | scans the tip only |
| Linter | path filter or glob | lints zero files |
| Formatter check | ignore list | checks nothing |
| Test selector | marker or sampling rate | runs an empty selection |
| Coverage | measured package list | measures an empty set |

- A gate whose input scope is set by a configuration parameter MUST be
  verified by the coverage it reports, not by its exit status. Where the
  tool emits a count of what it covered, read that count; where it does
  not, the gate SHOULD be wrapped so it fails on an implausibly small one
- Widening what a check examines MUST widen its scope parameter in the
  same change — the two are one edit, and splitting them leaves a gate
  that reads stronger than it is
- A reviewer MUST NOT accept a green run as evidence that a scope change
  took effect

`base/security/devsecops.md` and `platform/github.md` both require full
history for the secret scan specifically. This is the general rule that
the specific one is an instance of, and it holds regardless of which
platform or security template a project resolves.

### PR gate MUST mirror the deploy gate

- Any check the deploy/release workflow runs unconditionally MUST
  also run on the PR that could break it
- A gate that runs only post-merge is not a gate — it is a failure
  notification. By the time it fires, the broken code is already on
  the main branch
- When the deploy workflow runs `validate` (or equivalent) on every
  push to main, the PR workflow MUST run the same `validate` on
  every PR, regardless of which paths changed

### Mirror cross-cutting checks with an always-run job

When the deploy gate runs a deterministic check over a broader file
set than any PR job's path-filter (a formatter or linter over all
tracked files), mirror it on PRs with a dedicated always-run job —
not by widening an existing filter:

- A path-filter must enumerate every input the check reads; the next
  omitted path silently reopens the mirror gap. An always-run job is
  enumeration-free
- Keep output-measuring and language-scoped jobs (build, e2e, perf,
  per-language tests) path-filtered — promote only the cross-cutting
  deterministic steps to always-run
- Audit the whole command, not the step that broke. When adding the
  first mirror job for a composite gate command (`validate` = lint +
  format + typecheck + test + build), enumerate every step in the same
  pass and check each for inputs outside the path-filter's coverage.
  Mirror all exposed steps at once, or record which steps read only
  covered paths — an unaudited assertion that "the rest are covered"
  is how the second step surfaces later as its own incident
- This complements `quality-gates-skip-equivalent`: skip noisy output
  gates on PRs that provably cannot affect them; always run
  deterministic cross-cutting gates

### Green CI does not prove environment independence

CI runs on a clean checkout in one controlled environment. A passing
gate is NOT "no bugs" when the check's input or behavior depends on the
developer environment:

- The test reads the working-tree filesystem (`readdirSync`, `glob`)
  rather than tracked files (`git ls-tree`, explicit imports), so local
  scratch or gitignored artifacts change its input — CI never sees them
- The test depends on line endings, locale, timezone, filesystem case
  sensitivity, or available binaries
- The CI matrix omits the OS or runtime contributors use locally

For such tests: prefer tracked-files enumeration over filesystem walks;
gate a directory on an explicit anchor file so local-only artifacts are
filtered out; document the dependency in a comment at the test; and run
the gate locally on the dev OS at least once per session — local-first
catches what a clean-room CI cannot.

---

## Promote a resistant case to a gated tier
[ID: base-quality-gates-tier-promotion]

Projects with a tiered test/fixture system separate gated cases (a
golden-output or ground-truth regression that fails the build) from
ungated ones (spot-checked CI runs, confidence priors, informally
verified internal calls). When a bug surfaces in an ungated case and the
quick-fix candidates all probe-falsify against the existing gated
anchors, promote the affected case into the next-strictest tier before
attempting the deep fix. Promotion converts a silent failure into a
measurable metric, so the eventual fix lands against a regression target
instead of working blind.

The shape generalizes: promote a flaky integration test to a contract
test with a stronger oracle; promote a tutorial example to a CI-verified
example the first time doc-rot slips through; promote a manual smoke test
to an automated regression the first time a regression escapes. When a
fix does not fit one session, measure first by elevating the case a tier;
the deep fix follows with the metric as the gating signal.

## Generated-file staleness gate

[ID: quality-gates-staleness]

When a project commits generated artifacts (rendered docs, generated
configs, resolved template chains, code-from-schema output) AND uses
the `--check` convention from `base-docs`, the `--check` invocation
MUST be wired into CI as a required status check on the relevant
paths.

- Ask first whether the content should be generated at all. A block that
  is derivable tool output — a file listing, a resolved chain, a table of
  counts — and was written by hand is not stale in this gate's sense. It
  sits outside the gate's subject, so the gate reports nothing about it
  while looking as though it governs the file. Put it behind a marker and
  generate it, and the gate covers it from then on
- A gate MUST account for what it covers, not only for what it found. One
  file can hold a generated section and a hand-maintained block
  reproducing tool output, and `--check` reports that file in sync while
  the hand-written half is wrong. Enumerate the derivable blocks inside
  each artifact, not just the artifacts in the repository. This is
  `quality-gates-check-runs`'s "state what it inspected, not only what it
  found" one level up, applied to a gate rather than to a command
- A worked example is where this lands most often: a document explaining
  a tool by showing its output, in a file whose other sections are
  generated. The example is reproducible by one call and reads as prose,
  so nobody wires it up, and it drifts from the moment the tool's output
  changes
- A banner naming the regenerate command is decorative without the
  gate — a stale file looks identical to a fresh one, and the
  regenerator can silently break for months unnoticed
- A staleness gate that is never run on the relevant paths is the
  gate-by-omission anti-pattern named in `quality-gates-scope-agreement`
  — passing-because-skipped is not passing
- "The relevant paths" are three input classes, and the filter MUST
  enumerate all of them: the generator or source code, any source assets
  the render consumes (images, schemas, fixtures), and the committed
  artifacts themselves. A hand-edit or an incomplete regeneration is
  drift the gate exists to catch, and it lives in the artifact rather
  than the generator. This is the enumerate-every-input rule from
  `quality-gates-scope-agreement`, stated where a staleness filter is
  actually written
- A filter scoped to the generator alone is the common shape of that
  mistake, because the issue asking for the gate usually names the
  generator's path and a straight reading stops there
- The gate MUST fail when the committed artifact differs from a fresh
  render, exactly as it fails on lint or type errors

---

## Pair a checkable constraint with its check

[ID: quality-gates-pair-check]

`quality-gates-staleness` is one case of a general rule: a stated
constraint without its check is decorative. It looks enforced and
decays silently, because a violating artifact looks identical to a
clean one. A constraint that travels into a generated project (a
template output constraint inherited by a generated `CLAUDE.md`) carries
this risk furthest — the project inherits the rule with no protocol to
self-check it.

- An output constraint that is mechanically checkable MUST name its
  agent-runnable check — the command to run and the pass condition.
  Examples: "line length < 80" -> `awk 'length > 80' FILE`, output MUST
  be empty; "no raw HTML" -> `grep -nE '<[a-z]+>' FILE`, output MUST be
  empty
- State the check next to the rule it verifies — not in a separate
  tooling file the generated project never receives. The rule and its
  check MUST travel together, so every artifact generated from the
  template inherits both
- A constraint that is inherently subjective (imperative tone, "no
  explanatory prose", heading-case judgment) stays declarative and
  relies on review. Do NOT invent a brittle check to satisfy this rule
  (see `quality-gates-exclusions`)
- When the constraint guards a committed generated artifact, wire its
  check into CI as a required status check (see
  `quality-gates-staleness`)

A rule states intent; its paired check is what makes the intent hold.

---

## An ungated step beside a gated one reads as enforced

[ID: quality-gates-procedure-steps]

`quality-gates-pair-check` covers a constraint with no check, and
`quality-gates-check-runs` covers a check that was written and never
run. Neither covers a documented *procedure* whose steps are enforced
unevenly. Here the constraint is stated, the neighbouring check exists
and runs correctly, and what fails is the reader's inference across
steps — so no artifact is wrong until much later.

An operator runs the sequence top to bottom. One step's gate fires,
fails, is fixed, and passes, which is felt as the procedure checking the
work. The ungated step is simply not done and nothing reports it. A
procedure with no gates at all invites care; a procedure with one gate
invites trust in all of it.

- Enforcement is not transitive between adjacent steps. A gate covers
  the step it is attached to and says nothing about its neighbours,
  however the sequence reads
- Audit a procedure step by step, not procedure by procedure, recording
  against each step the check that enforces it or the fact that nothing
  does
- Either gate the remainder, or mark each unenforced step as unenforced
  where it is written, so an operator's confidence matches what is
  actually being verified
- Gate first the step whose omission cannot be corrected afterwards. The
  cost is asymmetric — re-cutting a published release to repair an
  omitted step is worse than the gap, so the archive keeps the gap
  permanently

---

## Run the check in the form it ships

[ID: quality-gates-check-runs]

`quality-gates-pair-check` requires a constraint to name its check. It
does not make that check work. A check that was written but never run is
the decoration the pairing rule exists to prevent, and it is worse than
none, because it looks enforced. A check that travels into a generated
project fails there, where nobody wrote it and nobody can debug it.

- A check MUST be run in the form it ships before the rule is merged.
  Extract it from the committed file and execute it — writing a check is
  not running it, and the file is a different medium from the editor
- A check MUST state what it inspected, not only what it found. A command
  that reached zero files and a command that found zero violations print
  the same thing. Report the count of inputs examined. The same rule for
  an assertion inside a test suite is `testing-negative-assertion-coverage`
- Where an empty result means drift rather than health, the check MUST
  report it as a failure — no journal entries found means the heading
  format moved, not that the file is ordered
- A check MUST emit ASCII. One that reports an offending character MUST
  print its code point, never the character, or it dies on the console
  encoding while reporting exactly what it exists to detect
- A fenced check MUST NOT be indented more deeply than the first
  indentation level of the code inside it. A renderer strips the fence's
  own indentation from every line that has it, so a block indented five
  spaces under a numbered step turns a four-space nested line into a
  three-space one and the extracted body stops compiling. Put the check
  flush with the margin and point to it from the step
- A check MUST be negative-controlled before merge: name the break modes
  it catches, confirm each one is flagged, and confirm that a valid input
  is not. A negative control that silently matches nothing has tested
  nothing
- The step that plants a break MUST itself be verified. Planting is an
  edit, and an edit that matched nothing exits zero and prints nothing, so
  a break that never landed and a check that never fired produce identical
  evidence — one says the check is blind, the other says it is fine.
  Confirm the planted input differs from the clean one, by a diff, a
  re-read, or a fixture the edit returns, before reading the run. Prefer
  planting into a throwaway copy whose clean state is known, so the
  confirmation is a comparison rather than an inspection
- Prefer a form that survives being copied. A heredoc whose delimiter is
  quoted passes escapes through untouched; an inline `-c` string loses
  them to shell expansion and arrives as a `SyntaxError`. Do not write the
  heredoc opener itself in prose — an extractor scanning for it reads the
  sentence as a check, the way a backticked directive is read as a real
  declaration
- A line continuation MUST be confirmed to have survived into the
  committed file. A trailing backslash can be dropped on the way from
  author to file, and when it is, the lines join and nothing reports it:
  the shell accepts the joined command, the compile gate accepts it, and
  only the text has changed. This is the one break mode that fails neither
  loudly nor closed, so reading the committed line is the whole check —
  every other break mode announces itself
- SHOULD avoid needing the confirmation. Fold the command onto one line —
  a fenced block is exempt from the width limit precisely so that is
  available — or bind its parts to shell variables. Where a continuation
  is genuinely the clearest form, keep it and verify it; the construct is
  not the defect, the silent loss is
- A violation count far larger than expected on a tree believed clean MUST
  be triaged as a possible defect in the check before it is worked as a
  backlog of fixes. A rule can be wrong rather than under-enforced

The first of these is itself mechanically checkable: every check embedded
in a rule file MUST compile when extracted the way a reader extracts it.
Adapt `ROOTS` to the files that carry the rules — the template tree in
this repository, the context file in a generated project:

```bash
py - <<'EOF'
import pathlib, re

# The files that carry rules and their checks.
ROOTS = ["templates"]

# A shipped check is a heredoc inside a fenced block. The fence may be
# indented under a list item, and a renderer strips that indent -- so
# strip it here too, or the extracted body will not compile.
FENCE = re.compile(r"^(\s*)```")
found, broken = 0, []
for root in ROOTS:
    for path in sorted(pathlib.Path(root).rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        n = 0
        while n < len(lines):
            opened = FENCE.match(lines[n])
            if not opened:
                n += 1
                continue
            indent, body, n = len(opened.group(1)), [], n + 1
            while n < len(lines) and not FENCE.match(lines[n]):
                line = lines[n]
                body.append(line[indent:] if not line[:indent].strip() else line)
                n += 1
            n += 1
            text = "\n".join(body)
            if "<<'EOF'" not in text:
                continue
            found += 1
            source = text.split("<<'EOF'", 1)[1].split("\nEOF", 1)[0].lstrip("\n")
            try:
                compile(source, str(path), "exec")
            except SyntaxError as error:
                broken.append((path, error.lineno, error.msg))

print("embedded checks found: %d" % found)
for path, lineno, msg in broken:
    print("%s: extracted body line %s does not compile: %s"
          % (path, lineno, msg))
if not found:
    print("no embedded checks found; the extraction pattern drifted")
EOF
```

Pass condition: the command reports the number of checks found and prints
nothing after it. An empty result is a failure too, since no checks found
means the extraction pattern drifted rather than the files being clean.

A companion locator for the continuation rule. It cannot detect a
continuation that was already lost — once joined, the line is
indistinguishable from one written that way — so it reports where the
risk is instead, and the list is what gets read against the source:

```bash
py - <<'EOF'
import pathlib, re

# The files that carry rules and their checks.
ROOTS = ["templates"]

FENCE = re.compile(r"^(\s*)```")
blocks, risky = 0, []
for root in ROOTS:
    for path in sorted(pathlib.Path(root).rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        n = 0
        while n < len(lines):
            opened = FENCE.match(lines[n])
            if not opened:
                n += 1
                continue
            indent, n = len(opened.group(1)), n + 1
            blocks += 1
            while n < len(lines) and not FENCE.match(lines[n]):
                line = lines[n]
                body = line[indent:] if not line[:indent].strip() else line
                if body.rstrip().endswith("\\"):
                    risky.append((path, n + 1))
                n += 1
            n += 1

print("fenced blocks inspected: %d" % blocks)
print("lines ending in a continuation: %d" % len(risky))
for path, number in risky:
    print("%s:%d" % (path, number))
if not blocks:
    print("no fenced blocks found; the extraction pattern drifted")
EOF
```

Pass condition: the command reports how many fenced blocks it inspected
and how many lines end in a continuation, then lists them. A non-zero
count is not a failure — it is the set to read against what was written.
Zero blocks inspected is a failure, since it means the pattern drifted
rather than the files carrying no checks.

---

## A check reports the moment it ran

[ID: quality-gates-check-timing]

`quality-gates-check-runs` requires that the check be run. It does not
say when, and a check reports on the state at the instant it executes.
Run before the change it gates, it reports the state before the change,
and nothing in that output distinguishes it from a run against finished
work: the clean result is evidence about a tree that no longer exists.

- Run a check AFTER the change it gates, never before. Where the check's
  subject is committed history, "after" means after committing rather
  than after editing — a branch whose work is staged and uncommitted
  reports exactly what a compliant branch reports
- A check that repairs, rewrites or otherwise alters its own subject
  answers differently on its second run, and only the first invocation
  is honest. Fix it to inspect without mutating; until then, every
  negative control of it MUST specify a single fresh invocation, or the
  control measures the repair rather than the defect
- State the moment where the operator reads the result — in the pass
  condition beside the command, not only in the prose around it. A pass
  condition that enumerates the causes of an empty result MUST include
  "the change is not in the subject yet", which is the cause a reader
  hits while writing the change rather than after it
- The failure is silent by construction, so it does not show up as
  flakiness. A gate that passed early and a gate that passed on the
  finished work are the same line of output, and the second run that
  would have contradicted it is the run nobody makes

---

## A check selects its subject, and the subject can move

[ID: quality-gates-check-selection]

A check can run, exit zero and report on the wrong thing. Two ways: it
picks an arbitrary member of a set it assumed had one element, or it
filters on a property that the violation itself changes. Both degrade
silently, and in both the change that breaks the check lives in a
different file and touches neither the rule nor the command, so no
reviewer of that change has reason to look.

- A check MUST select its subject, not a count or a position. Selecting
  "the latest", "the most recent", the first line or index zero is correct
  only while exactly one instance of the thing exists. Derive the selector
  from what is under test — the commit, the ref, the artifact name — never
  from ordering
- A check MUST NOT filter on a property that the violation it detects can
  change. Where a tool classifies artifacts (text or binary, tracked or
  ignored, parseable or not) and the check selects on that classification,
  state what a violating artifact's classification becomes, and add a
  second command covering the reclassified case with its own pass condition
- A check that has never failed, on a rule that was never enforced, MUST be
  treated as blind until a planted violation makes it fail (see
  `quality-gates-check-runs`). This is the only evidence that separates a
  satisfied check from one whose filter no longer matches anything

Selecting a CI run by recency is correct until a second workflow is added
for an unrelated reason, after which the check reports whichever finished
last and hides the other — a contributor can read a green scan and call a
red build good. Selecting it by the commit under review stays correct at
one workflow or five.

A line-ending gate that counts index entries classified as CRLF has the
sharper version of the problem. A file that acquires a NUL byte is
reclassified as binary, which stops it being normalised — the violation —
and simultaneously stops it matching the gate's own filter. The count
stays at zero for exactly as long as the defect is present, and starts
failing only once someone fixes it. The second command covers the
reclassified population, excluding the paths that are legitimately binary.

---

## Convention-as-test

[ID: quality-gates-convention-as-test]

A specific shape of `quality-gates-pair-check`: when a convention takes
the form "every record satisfying property X MUST share derived
artifact Y", its check is a test that enumerates the X-satisfying
records and asserts Y-equality across them.

- A written-down "if X then Y" invariant MUST be encoded as a test when
  Y is mechanically comparable. The test enumerates every record
  satisfying X and asserts they share Y. Examples: entries sharing a
  canonical product URL MUST share their generated image file; build
  outputs in one locale MUST share a glossary file
- The test gates the invariant at commit time. A prose convention is
  forgotten and the next divergent record lands undetected; the test
  fails loud, naming the pair that broke it
- This applies only to mechanically checkable invariants. Conventions
  that genuinely cannot be tested (subjective code style, prose tone)
  stay declarative (see `quality-gates-exclusions`)

---

## What NOT to gate

[ID: quality-gates-exclusions]

- **Docstring coverage for non-public functions** — enforcing docs on
  internal helpers creates busywork
- **Cyclomatic (McCabe) complexity as a hard gate** — too many false
  positives on legitimate complex logic; gate cognitive complexity
  with a ratchet instead (see `quality-gates-complexity`)
- **100% test coverage** — incentivizes meaningless tests; 80% is the
  practical sweet spot
- **Commit message format** — enforce in PR title via repository settings,
  not per-commit hooks; allow messy WIP commits on feature branches
- **Mutation score as a universal gate** — it is opt-in and advanced
  (see `quality-gates-mutation`); requiring it tree-wide spends the
  budget of a full suite rerun on the modules least likely to need it

---

## Periodic whole-tree audits

[ID: quality-gates-tree-audit]

Duplication and dead code are review-time rules, but a reviewer sees
the diff — and the twin of a pasted block usually lives outside the
diff. A rule whose violations are invisible in a diff needs a
scheduled whole-tree sweep, not a per-change gate.

- Duplication and dead-code detectors (pylint duplicate-code, jscpd,
  vulture) MUST NOT run as per-PR CI gates when the tree measures
  clean — both tool classes false-positive on legitimate patterns
  (look-alike scientific/CLI boilerplate for duplication,
  intentionally unused API parameters for dead code), so a per-PR
  gate means maintaining suppression lists forever to guard nothing
- Run them as a documented periodic whole-tree audit instead: record
  the exact commands and the last-run result in `docs/PLAYBOOK.md`,
  and run at epic boundaries and release points
- File audit findings as tickets rather than fixing on the spot —
  the audit is a discovery pass, not a change PR

---

## Tool constraints

[ID: quality-gates-constraints]

- All tools MUST be free for private repositories
- Prefer open-source tools over SaaS — no vendor lock-in
- Prefer tools with CI integration for the project's platform
- Prefer one tool per category — no redundant linters
- Stack templates define the specific tool per category
- Platform templates define the CI integration and SAST tool
