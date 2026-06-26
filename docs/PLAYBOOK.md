# Playbook

Operational reference for common tasks. Each section is a self-contained
procedure. See `CLAUDE.md` for authoring rules and `SPEC.md` for the
composition model.

---

## Add a new stack template

1. Identify the parent template(s) — check `manifest.yaml` for the closest
   existing stack and trace its `depends_on` chain
2. Create `stack/<prefix>-<name>.md`:
   - First line: `# Stack — <Full Name>`
   - Second line: `[DEPENDS ON: <parent1>, <parent2>, ...]`
   - One section per concern, each tagged `[ID: <name>]`
   - Use `[EXTEND: <id>]` to add rules on top of a parent section
   - Use `[OVERRIDE: <id>]` to replace a parent section entirely
   - Follow the canonical section structure (ADR-017): MUST sections
     are Stack, Commands, Project structure (pure libraries exempt
     from the last); name the language section `<Language> conventions`.
     SYS-06 gates the MUST tier on the resolved chain, so a derived
     stack may inherit a MUST section from its parent
3. Review for terminology carry-over from the source template:
   - All framework and runtime names match the target stack
   - CLI commands reference the correct package manager and tools
   - Server/runtime terms are accurate (e.g. WSGI vs ASGI vs
     process manager)
   - Language-specific vocabulary is correct (e.g. "packages" in Go,
     "crates" in Rust, "modules" in Python)
4. Register in `manifest.yaml`:
   ```yaml
   - id: stack-<name>
     file: stack/<prefix>-<name>.md
     depends_on:
       - <parent-id>
   ```
5. Add to the stack list in `SPEC.md` (alphabetical within category)
6. Add a row to the stacks table in `README.md`
7. Validate: attach `INTERVIEW.md` + new stack to an agent and review output

---

## Add a new base or layer template

1. Create the file in the correct layer directory:
   - `base/<name>.md` — cross-cutting, applies to all projects
   - `backend/<name>.md` — backend services only
   - `frontend/<name>.md` — frontend/UI projects only
2. Tag the file root with `[ID: <layer>-<name>]`
3. Tag every section with a unique `[ID: <layer>-<name>-<section>]`
4. Register in `manifest.yaml` under the correct layer key:
   ```yaml
   - id: <layer>-<name>
     file: <layer>/<name>.md
   ```
5. Update `docs/SPEC.md` — add to the directory listing for the relevant layer
6. Add `backend/<name>.md` (or frontend/) references in dependent stack
   `[DEPENDS ON: ...]` headers as appropriate

---

## Drain a downstream lesson into a template

A lesson sourced from one downstream project (a bug write-up, a session
retro) carries that project's domain in its framing. Vet it for
genericity before it becomes template content:

1. Extract the generic kernel — the rule that holds regardless of stack
   or domain. Strip project-specific nouns (entity, tool, and metric
   names)
2. If the kernel is genuinely cross-cutting, add it to the relevant
   `base/` or layer template per "Add a new base or layer template"
3. If a fragment only applies to one stack or domain, fold it as an
   *example* inside a generic rule — do not add it as standalone base
   content. Standalone one-stack content in a core-tier template loads
   into every chain and dilutes attention
4. Prefer extending an existing related rule over adding a parallel
   section — duplicate rules restated across templates are the same
   attention-dilution failure
5. Validate per "Validate a template change"

---

## Rename a template file

1. `git mv <old-path> <new-path>`
2. Update every `[DEPENDS ON: ...]` header that references the old path
3. Update `manifest.yaml` — change the `file:` field for the entry
4. Update `SPEC.md`, `README.md`, `INTERVIEW.md`
   — search for the old filename and replace
5. Update any `examples/` files that reference the old path
6. Verify with `git status` that no old references remain

---

## Rename a section ID

1. Change `[ID: <old>]` to `[ID: <new>]` in the source template
2. Search all template files for `[EXTEND: <old>]` and `[OVERRIDE: <old>]`
   — update every occurrence
3. Update `manifest.yaml` if the ID is referenced in `depends_on` lists
4. Update `manifest.yaml` if the concept maps to a template entry

---

## Author a new ADR

ADRs live in `docs/decisions/` and follow the schema defined in
`docs/decisions/010-adr-governance.md` (ADR-010). Use this workflow
for any significant architectural decision (new layer, naming
convention change, override model change, governance rule, etc.).

1. Copy the template:
   ```bash
   NNN=$(printf "%03d" $(($(ls docs/decisions/[0-9]*.md | wc -l) + 1)))
   cp docs/decisions/TEMPLATE.md docs/decisions/${NNN}-<slug>.md
   ```
   Slug is kebab-case, sentence-meaningful (e.g. `011-provenance-principle`).
2. Fill in the frontmatter — `id` (quoted string matching `NNN`),
   `status: Proposed` (or `Accepted` if the decision is already
   ratified), `date` (today, `YYYY-MM-DD`), `category` from the
   closed set in ADR-010, and `supersedes` / `superseded_by` lists.
3. Replace `# ADR-NNN: Title in sentence case` with the real title
   (colon form, sentence case).
4. Write the four sections in order — **Context** (why this
   decision is needed), **Decision** (what was decided, with
   RFC 2119 keywords), **Alternatives considered** (what was
   rejected and why), **Consequences** (downstream effects).
   Non-trivial decisions SHOULD include an inline ASCII diagram
   in the Decision section.
5. If this ADR supersedes an existing one: update the old ADR's
   frontmatter in the same PR — set its `status: Superseded`,
   refresh `date`, and add this ADR's id to its `superseded_by`
   list. This metadata-only update is the ONE allowed exception
   to ADR immutability; the prose body of the superseded ADR
   stays untouched.
6. Run `py tests/run_smoke.py ADR-01` to validate the frontmatter
   schema before opening the PR.
7. Open the PR. After merge, the ADR is immutable except for
   future supersession metadata updates.

---

## Generate a context file for a project

### Interview path

1. Open your agent (Claude Code recommended)
2. Attach `templates/INTERVIEW.md`
3. The agent explores what you want to build, asks a few clarifying questions,
   proposes a stack, and generates the file once you confirm
4. Place the generated file at the project root

### Direct path

1. Open your agent
2. Attach the relevant stack template (e.g. `templates/stack/python-flask.md`)
3. Provide your answers inline:
   ```
   Generate a CLAUDE.md. Name: X, owner: Y, repo: Z, database: PostgreSQL, auth: JWT.
   ```
4. Place the generated file at the project root

### Pre-resolved path (no shell access)

If the agent cannot run scripts, use the pre-resolved files in
`generated/`. Each file contains the full template chain for one stack:

1. Attach `generated/stack-flask.md` (or the relevant stack)
2. Attach `templates/base/core/agents.md` (output format)
3. Provide your answers and ask the agent to generate the file

### Path selection guide

| Interface | Recommended path | Why |
|-----------|-----------------|-----|
| Local agent (Claude Code, Codex CLI) | Interview or direct | Agent reads files from disk |
| Web portal (Claude.ai, ChatGPT) | Pre-resolved | Upload one file, no shell needed |
| REST API | Pre-resolved | Include `generated/<stack>.md` in prompt |

### Model limitations

| Stack category | Prompt size | Min context window |
|----------------|-------------|-------------------|
| Library / CLI | ~12K tokens | 32K |
| Static site | ~15K tokens | 32K |
| Backend service | ~25–50K tokens | 128K |
| Full-stack | ~40–60K tokens | 128K |

- Output token limit < 16K: generate section by section
- Output token limit 32K+: full inline file fits in one pass

---

## Validate a template change

1. **Smoke check**: run the automated structural checks — no agent required:
   ```bash
   py tests/run_smoke.py
   ```
   This verifies all `[DEPENDS ON: ...]` paths, unique IDs, `[EXTEND: ...]` /
   `[OVERRIDE: ...]` references, and `manifest.yaml` consistency in one pass.
2. **Agent check**: attach `INTERVIEW.md` + the changed template to an agent
   and review the output for coherence; or run the
   relevant E2E test if one exists:
   ```bash
   py tests/run_e2e.py STK-01   # example — replace with the relevant ID
   ```
   Reports are written to `tests/reports/` after every run.

---

## Run the test suite

```bash
py tests/run_smoke.py              # structural checks — seconds
py tests/run_e2e.py                # canary test (python-lib)
py tests/run_e2e.py --all          # all agent tests
py tests/run_e2e.py STK-01 FMT-01  # specific tests only
py tests/run_e2e.py --dry-run      # build prompts, skip agent calls
```

See `tests/CODIFICATION.md` for the ID scheme and `tests/INDEX.md` for the
full list of specs. Requires `py -m pip install pyyaml` for the manifest
check.

---

## Regenerate pre-resolved files

After editing any template or `manifest.yaml`, regenerate the cached
files in `generated/`:

```bash
py tools/resolve.py --generate     # regenerate all cached files
py tools/resolve.py --check        # verify they are up to date
py tools/sync.py                   # also regenerates via --check
```

The `generated/` files are committed to the repo so agents without
shell access can use them directly.

---

## Regenerate an example

Per ADR-016, the files in `examples/*/CLAUDE.md` are agent-generated
outputs, not hand-maintained. When a template in an example's chain
changes the output shape, regenerate the example — do not patch it by
hand.

1. Attach three inputs to a local agent:
   - the existing `examples/<name>/CLAUDE.md` — for the project brief
     (name, owner, repo, deployment, stack choices, architecture) to
     preserve
   - `generated/<stack>.md` — the resolved chain (the rules to apply);
     read any addon templates the example's stack source names but the
     chain does not include
   - `templates/base/core/agents.md` — the output models (inline,
     reference, or hybrid — keep the example's existing model)
2. Ask the agent to regenerate `examples/<name>/CLAUDE.md` in the
   six-section structure, keeping the concrete project identity and
   recording the generation inputs in a note near the top.
3. Verify: `py tests/run_smoke.py` (SYS-05 gates the §6.3 audit) and
   review the diff for coherence. Byte-for-byte reproduction is not
   expected — generation is non-deterministic.

---

## Run a 360-degree audit

Per `templates/base/workflow/360.md`, a 360 assesses the whole project
from independent stakeholder perspectives as parallel, context-isolated
subagents (the headless adaptation re-projects Quality into engineering
dimensions). Run one before a major release, after a milestone, or
quarterly.

- Store each audit as a dated report at `docs/audits/YYYY-MM-DD-360.md`
  (the §360-tracking option-b convention) — never the single-file
  `docs/360-audit.md` form; keep all history in the folder.
- Each report carries a scores table, the issues created, the current
  bottleneck, and per-dimension findings tables with a grade rationale.
- File a labelled issue for every actionable finding (CLAUDE.md §2.2)
  and reference it from the report.

---

## Submit a pull request

1. Ensure you are on a feature branch — never commit to `main` directly
2. Run the validation steps above for every changed template
3. Update all affected documents (`SPEC.md`, `README.md`, `manifest.yaml`) before committing
4. Commit with a conventional message:
   ```
   feat(stack): add go-echo template
   docs(spec): update backend layer listing
   ```
5. Push and open a PR — one concern per PR
6. After merge: delete the branch and pull `main`

---

## Release a new version

This repo has no version manifest (plain Markdown), so it follows the
no-build release variant from ADR-006: tag `main` directly via a GitHub
Release — there is no `chore: release` branch, commit, or PR.

1. Confirm the milestone's issues are all closed and `main` is green
   (`py tests/run_smoke.py` passes) and up to date (`git pull`)
2. Cut the release from `main` with a bare-version title and
   auto-generated notes:
   ```bash
   gh release create vA.B.C --title vA.B.C --generate-notes
   ```
   This tags `main` at HEAD and publishes notes built from the PRs
   merged since the previous tag
3. Close the `vA.B.C` milestone once the release is published
4. Add the session's `docs/dev-journal.md` entry **separately** — its
   own `docs(journal): ...` PR with **no milestone**, not part of the
   release

Projects with a version manifest (`package.json`, `pyproject.toml`,
etc.) instead follow the branch → bump → PR → merge → tag flow; see
ADR-006 and `base/core/git.md`.
