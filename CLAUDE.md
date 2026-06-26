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
tools/              # sync.py, resolve.py — sync and resolution scripts
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
py tools/resolve.py <stack-id>               # print resolved file list
py tools/resolve.py <stack-id> --concat      # print concatenated content
py tools/resolve.py --generate               # regenerate all cached files

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
- Issue titles: sentence case, imperative verb — no type prefix
  (labels carry the type)
- PRs are small and focused — one concern per PR; one approval
  required to merge
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
| `P3` | `#4BCE97` | Low — nice to have |
| `P4` | `#8590A2` | Backlog — someday |

#### Triage labels

| Label | Color | When to use |
|-------|-------|-------------|
| `duplicate` | `#C1C7D0` | Already tracked by another issue |
| `wontdo` | `#C1C7D0` | Acknowledged but will not be addressed |

### 2.3 Template naming convention

Stack files follow a `<prefix>-<name>.md` pattern:

| Prefix | Examples |
|--------|---------|
| `python-` | python-flask, python-fastapi, python-django, python-grpc, python-celery-worker |
| `go-` | go-lib, go-service, go-echo, go-grpc |
| `java-` | java-spring-boot, java-grpc |
| `node-` | node-express, node-nestjs |
| `nodejs-` | nodejs-lib |
| `spa-` | spa-react, spa-vue, spa-svelte |
| `full-` | full-nextjs, full-sveltekit |
| `mobile-` | mobile-flutter, mobile-react-native |
| `static-site-` | static-site-astro, static-site-hugo, static-site-tutorial |
| `iac-` | iac-terraform |
| `rust-` | rust-lib |
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
  picks one platform regardless of stack
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
- Keep line length under 80 characters
- No HTML — Markdown only
- A mechanically-checkable output constraint MUST name its
  agent-runnable check (command + pass condition); subjective
  constraints stay declarative (see `quality-gates-pair-check`)

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
- Do not duplicate content across documents — cross-reference
  instead
- Write in present tense — past or future tense indicates
  out-of-sync documentation

#### Decision logs

- Significant structural decisions (new layer, naming convention
  change, override model change) MUST be recorded as ADRs in
  `docs/decisions/`
- Each ADR documents: context, decision, alternatives considered,
  consequences
- Each ADR addresses exactly one concern — a separate concern gets
  its own ADR (multi-part decisions allowed within one concern)
- ADRs are immutable once merged — create a new ADR to supersede
  an old one. The ONE exception: `superseded_by` / `status` /
  `date` frontmatter fields on a previously-merged ADR MAY be
  updated when a new ADR supersedes it
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

Four files in `tests/`:

| File | Purpose |
|------|---------|
| `tests/lib.py` | Shared utilities (constants, file reading, report writing, arg parsing) |
| `tests/cases.py` | E2E test case definitions, grouped by area (STK, FMT, ITV, DPL) |
| `tests/run_smoke.py` | Smoke test runner (structural checks) |
| `tests/run_e2e.py` | E2E test runner (agent-based tests) |

```bash
py tests/run_smoke.py              # structural checks
py tests/run_smoke.py SYS-01       # run one check by ID

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
- CI runs smoke + gitleaks on PRs and on push to main
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
- If a change affects multiple documents, update all in the same PR
- Do not drift from the agreed scope without checking with the user
- When a path-based shell query (`test -f`, `ls`, `git -C <path>`,
  `git submodule status`, `git ls-tree`, etc.) returns an
  unexpected empty/negative, FIRST verify the working directory
  (`pwd`) — shell tool cwd persists across commands and an earlier
  `cd` may make "from the repo root" diagnostics false-negative

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
4. **Dev journal** — add a session entry to `docs/dev-journal.md`
   (date, tool, key changes, PRs merged, issues closed/created)
5. **ADRs** — record any architectural decisions in
   `docs/decisions/`
6. **Smoke tests** — run `py tests/run_smoke.py` and confirm all
   checks pass
7. **CLAUDE.md** — for each new convention/rule, apply the
   doc-placement decision tree in
   `templates/base/workflow/ai-workflow.md` (Doc placement decision
   tree section): evaluate code → ADR → README → PLAYBOOK →
   CLAUDE.md → memory in order. CLAUDE.md is the home ONLY if the
   agent MUST apply the rule on every turn.

   CLAUDE.md contains rules only — not changelogs, package
   architecture, per-feature progress, or session logs. Each rule
   fits on one line; if it needs a paragraph, write an ADR and
   leave a one-line pointer here. Evaluate items individually; do
   not batch-dismiss.
8. **README.md** — for each new command, dependency, or structural
   change, is it reflected? Name the section.
9. **docs/SPEC.md** — for each change to composition model or ID
   system, is it reflected? Name the section.
10. **templates/manifest.yaml** — for each template added, removed,
    or re-depended, is it registered? Name the entry.
11. **docs/ONBOARDING.md** — for each new tool, prerequisite, or
    setup step, is it documented? Name the section.
12. **docs/PLAYBOOK.md** — for each new command, script, or
    workflow added, is it documented? Name the section.
13. **Template feedback** — for each new pattern or convention
    introduced, explicitly state whether it is project-specific
    or reusable; if reusable, name the upstream template file
14. **Branch cleanup** — delete local branches that have been
    merged via PR: `git branch --merged main | grep -v main |
    xargs git branch -d`
15. **Flag gaps** — if any of the above cannot be completed, flag
    it to the user before closing
16. **Summary** — summarize what was done and what's next
