# solid-ai-templates

Composable, SOLID-inspired template system for generating AI agent context
files (CLAUDE.md, AGENTS.md, .cursor/rules/project.mdc, etc.) for any
project type.

## 1. Project

### 1.1 Overview

- **Name**: solid-ai-templates
- **Owner**: Imbra Ltd — Branimir Georgiev
- **Repo**: github.com/braboj/solid-ai-templates
- **Stack**: plain Markdown — no build step, no runtime dependencies
- **Output**: context files for Claude Code, Cursor, GitHub Copilot,
  Codex CLI
- **Model**: inline — all rules are self-contained in this file

### 1.2 Architecture

```
templates/          # All template source files
  base/             # Cross-cutting rules (core, security, infra, workflow, language)
  backend/          # Backend layer — HTTP, API, database, observability
  frontend/         # Frontend layer — UX, accessibility, CSS, SSG
  platform/         # CI and security tool mappings per hosting platform
  stack/            # Concrete stacks — extend base + layer templates
  INTERVIEW.md      # Agent-driven project setup interview
  manifest.yaml     # Machine-readable dependency graph
docs/               # Onboarding, playbook, decision logs, SPEC.md
examples/           # Complete generated context files (reference)
tests/              # Smoke and e2e test runners, specs, reports
tools/              # sync.py, resolve.py, audit_redundancy.py
generated/          # Pre-resolved template chains (one file per stack)
```

### 1.3 Commands

```bash
# No build step — all templates are plain Markdown
git clone https://github.com/braboj/solid-ai-templates.git

# Sync generated sections after editing templates/manifest.yaml
py tools/sync.py            # update SPEC.md, README.md, INTERVIEW.md, generated/
py tools/sync.py --check    # exit 1 if any file is out of sync

# Resolve dependency chain for a stack
py tools/resolve.py --list                    # list stack IDs
py tools/resolve.py --roots                   # list every root a project picks
py tools/resolve.py <stack-id>               # print resolved file list
py tools/resolve.py <stack-id> --concat      # print concatenated content
py tools/resolve.py --generate               # regenerate all cached files

# Audit redundant rules across resolved chains
py tools/audit_redundancy.py                 # exact in-chain duplicates
py tools/audit_redundancy.py --near          # include near-duplicates
py tools/audit_redundancy.py --check          # CI gate — fail on new dups

# To generate a context file for a project:
# 1. Open your agent
# 2. Attach templates/INTERVIEW.md and the relevant stack template
#    (or use generated/<stack-id>.md for the pre-resolved chain)
# 3. Ask the agent to generate CLAUDE.md (or AGENTS.md, etc.)
```

## 2. Code conventions

### 2.1 Git

- Branch: `main` (protected) — never commit directly
- Branch naming: `feat/<scope>`, `fix/<scope>`, `docs/<scope>`,
  `chore/<scope>`
- Commits: `<type>(<scope>): <summary>` — types: feat, fix, chore,
  docs, refactor
- PR titles: `<type>(<scope>): <summary> (#issue)` — same format
  as commits, with issue number(s) at the end
- A single-commit PR MUST carry the issue number in the commit subject
  too: GitHub squashes using the PR title only when the branch holds two
  or more commits, and the commit subject when it holds one
- Issue titles: sentence case, imperative verb — no type prefix
  (labels carry the type)
- PRs are small and focused — one concern per PR, merged once its
  checks pass; no approving review is required, and none is enforced
- After a PR is merged, delete branch and pull main before starting
  new work
- Do not commit `.idea/`, editor config, or any generated output

### 2.2 Issue labels

Every issue MUST have exactly one type label and one priority label,
applied at creation — never create a ticket unlabeled. Triage labels
are terminal — applied when closing without action.

#### Type labels (pick one)

| Label | Color | When to use |
|-------|-------|-------------|
| `bug` | `#C9372C` | Defect in existing functionality |
| `epic` | `#9F8FEF` | Large initiative spanning multiple tasks |
| `task` | `#579DFF` | Atomic implementable work |
| `spike` | `#6CC3E0` | Research or exploration — output is a decision |
| `incident` | `#AE2E24` | Production outage or degradation affecting users now |

#### Priority labels (pick one)

| Label | Color | Meaning |
|-------|-------|---------|
| `P0` | `#E06C00` | Critical — blocks everything |
| `P1` | `#FCA700` | High — must fix before next milestone |
| `P2` | `#EED12B` | Medium — important but not blocking |
| `P3` | `#4BCE97` | Low — nice to have, including trivial |

There is no fifth band. Deferral is carried by an empty milestone
field, not by a label — milestoned means planned, unmilestoned means
backlog (ADR-024).

#### Triage labels

| Label | Color | When to use |
|-------|-------|-------------|
| `duplicate` | `#C1C7D0` | Already tracked by another issue |
| `wontdo` | `#C1C7D0` | Acknowledged but will not be addressed |

### 2.3 Template naming convention

Stack files follow a `<prefix>-<name>.md` pattern:

| Prefix | Examples |
|--------|---------|
| `python-` | python-flask, python-fastapi, python-django, python-grpc |
| `go-` | go-lib, go-service, go-echo, go-grpc |
| `node-` | node-express, node-nestjs |
| `nodejs-` | nodejs-lib |
| `static-site-` | static-site-astro, static-site-tutorial |
| `c-` | c-embedded |

Stacks without a variant use a bare name (e.g. `htmx.md`).

### 2.4 Inheritance model

```
base/ ──┬── frontend/ ──┐
        ├── backend/  ──┼── stack/
        └── platform/ ──┘
```

- Every stack declares `[DEPENDS ON: ...]` at the top
- Sections are tagged `[ID: ...]`, extended with `[EXTEND: ...]`,
  replaced with `[OVERRIDE: ...]`
- Platform templates are orthogonal to the stack chain — a project
  picks one platform regardless of stack, and it resolves as its own
  root, so its guaranteed context is the core tier plus its own
  `depends_on` tree and nothing from the stack (ADR-035); the same
  holds for every opt-in extra
- `templates/manifest.yaml` is the machine-readable dependency graph

### 2.5 Adding a new stack template

1. Create `templates/stack/<prefix>-<name>.md` following an existing
   file of the same category
2. Add `[DEPENDS ON: ...]` at the top — list every template this
   extends
3. Tag every section with `[ID: <name>]` or `[EXTEND: <id>]` /
   `[OVERRIDE: <id>]`
4. Register in `templates/manifest.yaml` under `stacks:` with
   `depends_on`, `description`, `label`, and `layer` fields
5. Run `py tools/sync.py` — updates SPEC.md, README.md, INTERVIEW.md
6. Add an example in `examples/<name>/CLAUDE.md` if the stack is
   concrete — generate it via the pipeline per ADR-016 (see PLAYBOOK
   "Regenerate an example"); never hand-write it

### 2.6 Adding a new base or layer template

1. Create the file in the correct directory:
   - `templates/base/core/` — foundation (git, docs, quality, etc.)
   - `templates/base/security/` — security rules
   - `templates/base/infra/` — CI/CD, containers, deployment
   - `templates/base/workflow/` — session protocol, issues, gates
   - `templates/base/language/` — language-specific rules
   - `templates/base/data/` — data modeling, quality, governance, migration
   - `templates/backend/` — backend services
   - `templates/frontend/` — frontend/UI projects
   - `templates/platform/` — CI platform mappings
2. Tag the file with `[ID: <layer>-<name>]`
3. Tag every section with a unique `[ID: ...]`
4. Register in `templates/manifest.yaml` under the correct layer
   key with a `description` field
5. Run `py tools/sync.py` — updates SPEC.md directory listings
6. Reference from dependent stack templates via `[DEPENDS ON: ...]`

### 2.7 Template authoring rules

- Sections use imperative, direct language: "Use X", "Never Y",
  "Always Z"
- No explanatory prose in rule lists — rules only
- Use `[ID: ...]` on every section that another template might
  EXTEND or OVERRIDE
- Optional sections are marked `(if applicable)` in the heading
- Keep line length under 88 characters, the width declared in
  `.markdownlint.json` for Markdown and `.editorconfig` for Python —
  exempt: table rows, fenced code, single-line `[DEPENDS ON: ...]`
  directives, and unbreakable tokens (long URLs / Markdown link
  targets)
- No HTML — Markdown only
- A mechanically-checkable output constraint MUST name its
  agent-runnable check (command + pass condition); subjective
  constraints stay declarative (see `quality-gates-pair-check`)
- A shipped check states its command in a fenced block, with the pass
  condition in prose beside it — a command typed into a sentence cannot
  be extracted, counted or run. A sentence naming no command states no
  check at all (ADR-031)
- A check that derives a comparison baseline by running a command MUST
  verify the command produced one and refuse when it did not — the
  refusal is a finding, never exit 3; see `base-quality`
- Never name another file's section ID in running prose unless that file
  resolves into every chain carrying yours — state the substance inline
  instead; SYS-11 checks it per chain (see SPEC.md "Naming another file's
  section in prose")
- When a rule could live in either of two templates, measure both files'
  chain reach first and put it in the wider one, leaving the narrower to
  defer — the reverse gives the consumers in the gap a deferral and no
  rule (ADR-028)
- Stack templates follow the canonical section structure (ADR-017):
  MUST sections are Stack, Commands, Project structure (pure
  libraries exempt from the last); see ADR-017 for SHOULD/MAY tiers,
  ordering, and the `<Language> conventions` naming — gated by SYS-06

### 2.8 manifest.yaml

- Every template file MUST have a corresponding entry in
  `templates/manifest.yaml`
- IDs MUST be unique across all layers
- `depends_on` lists MUST reference valid IDs — no dangling
  references
- Stack entries go under `stacks:`, base under `base:`, layer under
  `backend:`, `frontend:`, or `platform:`

### 2.9 Documentation

#### Standard documents

| File | Purpose |
|------|---------|
| `README.md` | Public-facing overview, quick start, stacks table, agents table |
| `CLAUDE.md` | AI agent context and project rules (this file) |
| `docs/SPEC.md` | System design, composition rules, inheritance model, precedence |
| `templates/manifest.yaml` | Machine-readable dependency graph for all templates (single source of truth for descriptions, labels, layers) |
| `docs/ONBOARDING.md` | Onboarding guide for new contributors |
| `docs/PLAYBOOK.md` | Operational reference — how to add templates, run interviews, validate output |
| `CHANGELOG.md` | Released versions and what changed in each; versions up to v2.63.0 are in the GitHub Releases (ADR-029) |
| `SECURITY.md` | Private disclosure route, supported versions, scope, acknowledgement window |
| `CONTRIBUTING.md` | What a change is checked against — gates, manifest duty, authoring rules, branch and commit form |
| `docs/design/` | Design documents about the library itself — the design record, agent-context tradeoffs, template-content quality (see SPEC "Design documents") |

#### Documentation rules

- Before every PR, update all relevant documents:
  - `CLAUDE.md` — if architecture, naming conventions, or authoring
    rules change
  - `README.md` — if the stacks table, project structure, or quick
    start change
  - `docs/SPEC.md` — if the composition model, inheritance rules,
    or ID system change
  - `templates/manifest.yaml` — if any template is added, removed,
    renamed, or re-depended
  - `docs/PLAYBOOK.md` — if the workflow for generating or
    validating changes
  - `docs/ONBOARDING.md` — if prerequisites or first steps change
  - `CHANGELOG.md` — add an `Unreleased` entry for any change a
    consuming project would notice, in the same PR that makes it. A
    change needing no entry says so in the PR body rather than staying
    silent; a template change almost always needs one, and a change to
    this repo's own tooling or tests usually does not. Keep each entry
    within the forty-word bound `base-docs` declares, checked in that PR
    rather than at the cut
- Do not duplicate content across documents — cross-reference
  instead
- Write in present tense — past or future tense indicates
  out-of-sync documentation

#### Decision logs

- Apply the ADR threshold in `templates/base/core/docs.md`: consequential,
  durable architectural choices with meaningful alternatives need a record.
  Routine naming, moves, check refinements, and compliance repairs do not.
- Each ADR documents: context, decision, alternatives considered,
  consequences
- One coherent architectural decision may cover related choices across
  several issues or PRs; do not require a record per implementation concern.
- What is immutable in a merged ADR is the decision — the claims
  made in Context, Decision, Alternatives considered and
  Consequences. Preserve those claims as history; routine refinements update
  current docs and the PR, while material architectural changes need a new ADR.
  Supersession
  metadata (`superseded_by` / `status` / `date`) and format-only
  edits that move no claim are both permitted; see `base-docs`
  Decision logs for the test and the evidence it requires
- Where a merged ADR and the templates disagree, the templates
  govern and the ADR stands as history. This repository owns the
  rules it applies, so a record describes a rule rather than
  departing from one, and a correction is complete when the rule is
  right in the templates — whether or not a new ADR was written. A
  project consuming the templates declares its own ordering, per
  `base-docs`
- ADR schema is governed by ADR-010 — YAML frontmatter required
  (`id` as quoted string, `status` in {Proposed, Accepted,
  Superseded}, `date` YYYY-MM-DD, `category` in {composition,
  templates, tooling, process, release}, reciprocal `supersedes` /
  `superseded_by` links). Copy `docs/decisions/TEMPLATE.md` when
  authoring a new ADR; `py tests/run_smoke.py ADR-01` enforces
  the schema

#### Rule language

All rules in templates use RFC 2119 keywords:

| Word | Meaning |
|------|---------|
| MUST | Absolute requirement |
| MUST NOT | Absolute prohibition |
| SHOULD | Recommended — deviations require justification |
| MAY | Optional |

## 3. Quality

### 3.1 Testing

Eight files in `tests/`:

| File | Purpose |
|------|---------|
| `tests/lib.py` | Shared utilities (constants, file reading, report writing, arg parsing) |
| `tests/cases.py` | E2E test case definitions, grouped by area (STK, FMT, ITV, DPL) |
| `tests/run_smoke.py` | Smoke test runner (structural checks) |
| `tests/run_e2e.py` | E2E test runner (agent-based tests) |
| `tests/providers.py` | Model backends the e2e runner selects between |
| `tests/conformance.py` | Disposition per embedded check — run here, or skip with a reason |
| `tests/run_conformance.py` | Runs the templates' own embedded checks against this repository |

```bash
py tests/run_smoke.py              # structural checks
py tests/run_smoke.py SYS-01       # run one check by ID

py tests/run_conformance.py        # the templates' checks, against this repo
py tests/run_conformance.py --list # dispositions only, run nothing

py tests/run_e2e.py                # canary only (python-lib, needs API key)
py tests/run_e2e.py --all          # all tests (live, needs API key)
py tests/run_e2e.py --area=STK     # run all stack tests
py tests/run_e2e.py STK-01 FMT-01  # run specific tests by ID
py tests/run_e2e.py --fail-fast    # stop on first failure
py tests/run_e2e.py --dry-run      # print prompts, skip execution
```

- Both runners write a timestamped Markdown report to
  `tests/reports/` after every run (gitignored)
- Spec files live in `tests/specs/` — see `tests/CODIFICATION.md`
  for the ID scheme and `tests/INDEX.md` for the full list
- CI runs smoke, conformance, `sync.py --check`, `resolve.py --check`,
  the redundancy audit and gitleaks on PRs and on push to main
- Live e2e calls an LLM via the API — run manually on the
  dev machine for functional validation
- To validate a new template: run `py tests/run_smoke.py` and
  attach `templates/INTERVIEW.md` + the new stack to an agent to
  confirm coherent output

## 4. Identity

Not applicable — this project has no design system or brand voice.

## 5. Review process

### 5.1 Code review

Priority order (highest first):
1. **Correctness** — do `[DEPENDS ON]`, `[EXTEND]`, `[OVERRIDE]`
   references resolve? Does the manifest entry match?
2. **Completeness** — are all required documents updated (see 2.9)?
3. **Clarity** — are rules imperative and unambiguous?
4. **Conventions** — does the template follow authoring rules
   (see 2.7)?

### 5.2 Structure audit

Run `py tests/run_smoke.py` before every PR. It checks:
- All `[DEPENDS ON: ...]` reference existing files
- All `[EXTEND: ...]` and `[OVERRIDE: ...]` reference valid IDs
- All EXTEND/OVERRIDE targets are reachable in the resolved chain
- No chain overrides one section ID from two templates
- All manifest entries point to existing files
- All template files have a manifest entry
- No duplicate IDs across layers
- All stacks resolve to valid, non-empty file lists
- All resolved chains include core tier files
- Prompt builds for all stacks

## 6. Session protocol

### 6.1 Startup

1. Read `CLAUDE.md` (this file) and `docs/SPEC.md`
2. Check for stale branches: run `git branch --no-merged main`
   and flag any unmerged branches to the user — they may contain
   lost work
3. Confirm the scope with the user before making changes
4. If the task is ambiguous, ask: "What is the specific deliverable
   for this session?"

### 6.2 During the session

- Run `py tests/run_smoke.py` after any template or manifest change
- Adding a fenced `bash`/`python` block to a template MUST add its
  disposition in `tests/conformance.py` — run it here, or skip it with
  the reason it does not apply. `py tests/run_conformance.py` fails on a
  block with no entry. A block whose pass condition declares a threshold
  takes a predicate, not a judgement; a judgement disposition MUST state
  what takes a person, and MUST name the check in
  `tests/reading-budget.txt` beside that reason. The runner fails on a
  judgement stating neither
- A conformance run is NOT clean until its judgement readings are read —
  `0 failed` counts only the automatic verdicts. The `not applicable`
  count is not among them: those checks answered by exiting 3 and need no
  reader (PLAYBOOK, "Run the test suite")
- Run `py tools/sync.py` after the LAST template edit of a change, not
  the first — smoke does not read `generated/`, so a chain regenerated
  before a later edit is stale and surfaces only in CI
- If a change affects multiple documents, update all in the same PR
- Do not drift from the agreed scope without checking with the user
- When a path-based shell query (`test -f`, `ls`, `git -C <path>`,
  `git submodule status`, `git ls-tree`, etc.) returns an
  unexpected empty/negative, FIRST verify the working directory
  (`pwd`) — shell tool cwd persists across commands and an earlier
  `cd` may make "from the repo root" diagnostics false-negative
- Verify the branch, not only the directory, before trusting a
  measurement — a parallel session shares this checkout and moves HEAD,
  so take any figure you will report from a worktree pinned to an
  explicit ref
- A control's plant MUST take a form the check actually inspects: a
  prose section proves nothing against a detector that fingerprints
  bullet lines, and the clean result reads as the check holding
- The inverse holds too: when a probe returns an unexpected *uniform*
  positive — every repository carries the file, every case passes —
  validate it against a control that MUST fail before believing it. A
  failed call is not always visible in the output: `gh api` prints the
  404 body to stdout, so `gh api <missing-path> --jq '.name'
  2>/dev/null` yields a non-empty string and reads as a hit for every
  input
- Stage or commit before running a control that mutates the tree. The
  revert step is `git checkout -- <path>`, which restores from the index
  and discards unstaged work without saying so — an uncommitted edit to
  the file under test is exactly what the control destroys
- A control MUST assert its mutation landed before its result is read.
  A pattern written with the wrong line endings edits nothing, the check
  then reports clean because the tree never changed, and that reads as
  the guard holding when it was never exercised
- A control MUST also force the path under test to run. Satisfying the
  precondition is not the same as exercising the code: a tool that
  writes nothing to a file already in its target state reports clean
  because it never executed, and that reads as the tool being innocent
  of what it is suspected of
- Report only measurements this session took. An issue states its
  measurement against the tree on its filing date; repeating that figure
  in a commit message or pull request body asserts it about the tree
  now, and the two differ precisely when the defect has since been fixed

### 6.3 End of session

When the user signals end of session ("wrap up", "let's finish",
"end session", "close out", or similar), print the full checklist
below and execute each item sequentially. Mark each item done
(with result) before moving to the next. Do not batch, skip, or
summarize — visible sequential execution prevents missed steps.

1. **Commits and push** — all changes committed and pushed (via
   PR if branch-protected)
2. **Close issues** — close completed issues (verify auto-close
   worked)
3. **Epic checklists** — update epic checklists if relevant
4. **ADRs** — record any architectural decisions in
   `docs/decisions/`
5. **Smoke tests** — run `py tests/run_smoke.py` and confirm all
   checks pass
6. **CLAUDE.md** — for each new convention/rule, apply the
   doc-placement decision tree in
   `templates/base/workflow/ai-workflow.md` (Doc placement decision
   tree section): evaluate code → ADR → README → PLAYBOOK →
   CLAUDE.md → memory in order. CLAUDE.md is the home ONLY if the
   agent MUST apply the rule on every turn.

   CLAUDE.md contains rules only — not changelogs, package
   architecture, per-feature progress, or session logs. Keep necessary
   qualifiers; paragraph length does not require an ADR.
7. **README.md** — for each new command, dependency, or structural
   change, is it reflected? Name the section.
8. **docs/SPEC.md** — for each change to composition model or ID
   system, is it reflected? Name the section.
9. **templates/manifest.yaml** — for each template added, removed,
   or re-depended, is it registered? Name the entry.
10. **docs/ONBOARDING.md** — for each new tool, prerequisite, or
    setup step, is it documented? Name the section.
11. **docs/PLAYBOOK.md** — for each new command, script, or
    workflow added, is it documented? Name the section.
12. **Template feedback** — consider a demonstrated shared defect or recurring
    need, reconcile existing issues, and act within the authorized scope.
    A reusable-looking preference alone requires no ticket or ADR.
13. **Branch cleanup** — delete local branches whose PRs have merged,
    verified against the PR record: `gh pr view <N> --json
    state,headRefOid` must report `MERGED`, then `git branch -D`.
    `git branch --merged` cannot see a squash merge and silently
    matches nothing; a `headRefOid` that differs from the local tip
    usually means `gh pr update-branch` rewrote the remote head, so
    inspect it rather than assume unpushed work
14. **Flag gaps** — if any of the above cannot be completed, flag
    it to the user before closing
15. **Dev journal** — add a session entry to `docs/dev-journal.md`
    (date, tool, key changes, PRs merged, issues closed/created). This
    item sits after flagging gaps because it is the only one whose output
    is a record of the others, and item 14 resolves into a change whenever
    a flagged gap has a fix small enough to apply on the spot. Written
    earlier, its merged-pull-request, issue and upstream lines are
    incomplete by construction, and an entry's account is fixed once
    written, so the correction costs a second entry for one session.
    Where the checklist runs twice in a session — a release wrap-up, then
    a close-out — only the last pass writes the entry; the earlier one
    records that the session owes it
16. **Summary** — summarize what was done and what's next

## 7. Communication

Defaults from `base-communication`, inlined per this project's inline
model. A downstream project MUST preserve these and MAY add its own
shorthand verbs.

- Concise, direct answers — no filler, no preamble, no restating the
  request before answering
- State your preferred option after presenting suggestions — do not make
  the user choose when you have a view
- Ask before assuming scope on an ambiguous instruction — do not silently
  expand it

### 7.1 Shorthand verbs

| Verb | Meaning |
|------|---------|
| `next` | Move to the next item without asking for confirmation |
| `stop` | Stop working; this does NOT mean save or commit |
| `yes` | Proceed; do not summarise what you are about to do, just do it |

### 7.2 Project additions

- Brevity applies to analysis, reports and audit findings, not only to
  edit recaps — a long answer is not more thorough, it is harder to act on
- When the user says a finding is unclear, restate it concretely with a
  worked example; do not defend the original wording
