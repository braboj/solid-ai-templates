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

### Recommended lint plugins

- **eslint-plugin-sonarjs** — detects cognitive complexity, duplicate
  branches, identical expressions, and other code smells that standard
  ESLint rules miss; SHOULD be added to any TypeScript/JavaScript project

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

Stack templates MAY add additional thresholds (e.g. Lighthouse scores).

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

### PR gate MUST mirror the deploy gate

- Any check the deploy/release workflow runs unconditionally MUST
  also run on the PR that could break it
- A gate that runs only post-merge is not a gate — it is a failure
  notification. By the time it fires, the broken code is already on
  the main branch
- When the deploy workflow runs `validate` (or equivalent) on every
  push to main, the PR workflow MUST run the same `validate` on
  every PR, regardless of which paths changed

---

## What NOT to gate

[ID: quality-gates-exclusions]

- **Docstring coverage for non-public functions** — enforcing docs on
  internal helpers creates busywork
- **Cyclomatic complexity thresholds** — too many false positives on
  legitimate complex logic; rely on lint warnings instead
- **100% test coverage** — incentivizes meaningless tests; 80% is the
  practical sweet spot
- **Commit message format** — enforce in PR title via repository settings,
  not per-commit hooks; allow messy WIP commits on feature branches

---

## Tool constraints

[ID: quality-gates-constraints]

- All tools MUST be free for private repositories
- Prefer open-source tools over SaaS — no vendor lock-in
- Prefer tools with CI integration for the project's platform
- Prefer one tool per category — no redundant linters
- Stack templates define the specific tool per category
- Platform templates define the CI integration and SAST tool
