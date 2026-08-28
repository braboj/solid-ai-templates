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
2. Pick the target by **measured chain reach**, not by the home the
   issue suggests — and know which kind of template you are measuring:

   ```bash
   # how many of the 17 stacks resolve a candidate file?
   for s in $(py tools/resolve.py --list); do
     py tools/resolve.py "$s" | grep -q 'core/review.md' && echo "$s"
   done | wc -l
   ```

   A **chain template** carries rules the generated project follows.
   Reach is the criterion for it, and a rule in one that no chain
   resolves reaches no generated context file.

   A **pipeline template** carries rules about generating or consuming a
   context file, and `templates/INTERVIEW.md` reads it directly rather
   than any stack resolving it. Its chain reach is structurally 0 and
   says nothing about whether the rule lands: `base/core/agents.md`
   measures 0/17 and shapes every file the pipeline generates. Recognise
   one by asking what reads it — a stack, or INTERVIEW.md. `platform/`
   templates sit outside the chain for a third reason: a project picks
   one regardless of stack.

   A filed issue's suggested home is a hypothesis — it is usually
   written from the downstream project, without running this. Where a
   rule needs universal reach but applies only sometimes, put it in a
   high-reach template behind an `(if applicable)` heading rather than
   in a low-reach one. Where a rule is one case of a contrast whose
   other cases live in a low-reach file, it stays with them: a case that
   cannot be read without the ones it is defined against is not made
   more useful by moving it somewhere better resolved
3. If the kernel is genuinely cross-cutting, add it to the relevant
   `base/` or layer template per "Add a new base or layer template"
4. If a fragment only applies to one stack or domain, fold it as an
   *example* inside a generic rule — do not add it as standalone base
   content. Standalone one-stack content in a core-tier template loads
   into every chain and dilutes attention
5. Prefer extending an existing related rule over adding a parallel
   section — duplicate rules restated across templates are the same
   attention-dilution failure
6. Validate per "Validate a template change"

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
7. If the ADR **removes** a concept, sweep for prose that still
   assumes it — in `templates/` and in open issue bodies:
   ```bash
   grep -rn "<concept>" templates/ docs/
   gh issue list --state open --limit 100 --json number,title,body \
     --jq '.[] | select(.body | test("<concept>")) | "#\(.number) \(.title)"'
   ```
   A queued issue proposing template text that reintroduces the
   removed concept passes review on its own terms and undoes the
   ADR when implemented. Fix the issue body, do not rely on
   catching it at implementation time.
8. Open the PR. After merge, the ADR is immutable except for
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

## Audit redundancy

A rule stated in two active sections of the same resolved chain dilutes
the agent's attention (see `docs/meta/template-content-quality.md`). The
audit scans every chain and reports duplicates, excluding those the
override model legitimately produces (one section `[OVERRIDE]`s the
other):

```bash
py tools/audit_redundancy.py           # exact in-chain duplicates
py tools/audit_redundancy.py --near    # also paraphrase near-duplicates
py tools/audit_redundancy.py --check   # exit 1 if any exact duplicate
```

Run it before opening a template PR and when consolidating rules. A
finding is not automatically a defect — a duplicate may be intentional
(e.g. a rule a base template needs when used standalone). Judge each
against the single-source principle, then either trim the restatement
(prefer the parent/owner template) or accept it with a reason.

`--check` runs in CI as a ratchet: it fails on any exact duplicate not
in the tool's `BASELINE` allowlist, so new redundancy is blocked while
the known duplicates clear through their owning issues (currently the
frontend pair, #624). When you resolve a baselined duplicate, remove
its `BASELINE` entry in `tools/audit_redundancy.py` — `--check` reports
any entry that no longer applies.

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
  (per §360-tracking) — this is the only audit location; never use a
  single-file `docs/360-audit.md` history. All audit history lives in
  the folder.
- Each report carries a scores table, the issues created, the current
  bottleneck, and per-dimension findings tables with a grade rationale.
- File a labelled issue for every actionable finding (CLAUDE.md §2.2)
  and reference it from the report.

---

## Submit a pull request

1. Ensure you are on a feature branch — never commit to `main` directly
2. Run the validation steps above for every changed template
3. Update all affected documents (`SPEC.md`, `README.md`, `manifest.yaml`) before
   committing
4. Commit with a conventional message:
   ```
   feat(stack): add go-echo template
   docs(spec): update backend layer listing
   ```
5. Push and open a PR — one concern per PR
6. After merge: delete the branch and pull `main`

Where a cut carries more than one pull request, every branch after the
first goes `BEHIND`. Each merge regenerates `generated/`, so the second
branch carries pre-resolved chains built from a tree that lacks the
first one's change. Git reports the branch `MERGEABLE` — the edits fall
in different regions of the same files — so nothing warns that the
chains are stale, and smoke does not read `generated/` either. CI is the
first signal.

Recover it with `gh pr update-branch`, never a rebase and force-push.
Then re-run both staleness gates on the updated branch, because
mergeable is not the same claim as current:

```bash
gh pr update-branch <number>
git pull
py tools/sync.py --check
```

Pass condition: the gate prints `All files in sync` **after** the
update, having listed every generated chain it compared. `sync.py
--check` is the whole gate — it covers `generated/` as well as the three
generated documents, so there is no second command to run. Run it before
the update instead and it reports the previous state, which reads as a
pass.

`tools/resolve.py` takes no `--check`; given one it falls through to
`--list`, prints the stack IDs and exits `0`. An unknown flag on that
tool is indistinguishable from a clean gate.

---

## Groom the backlog

Run this before scoping a cut. Nothing surfaces the backlog on its own —
an unmilestoned issue is triaged, not untriaged, so no view reports it and
no gate asks about it.

1. Re-read the whole unmilestoned set. Milestoned means planned into that
   cut; unmilestoned means backlog, and the only way to see it is to list
   it:
   ```bash
   gh issue list --state open --limit 200 --json number,title,milestone --jq '.[] | select(.milestone == null) | [.number, .title] | @tsv'
   ```
2. **Verify each issue's claims against the tree before grooming, not
   after.** An issue is written against the tree as it stood on its
   filing date, and grooming a claim that has since moved plans work that
   does not exist. Measure the claim, then annotate the issue with what
   the measurement found and its date
3. Cluster by target file. Issues touching one section are one pull
   request rather than several, and the clustering is visible only once
   the claims are verified — two issues can name the same file and want
   changes that do not compose
4. Scope the cut from the clusters, then create the milestone. A theme
   falls out of what the groom found; choosing a theme first selects
   issues to fit it. The title is `vA.B.C — <theme>` and the description
   enumerates the issues; the release tag message quotes that theme, so
   a milestone titled with a bare version leaves the tag with nothing to
   quote

Grooming produces annotations and a milestone, not edits. An issue whose
measurement shows it is narrower, wider or wrong as filed is annotated
with that finding and left open — restating the scope is the implementer's
step, and `base-review` covers the shapes it takes.

### Sweep merged commits for still-open issues

An issue whose work merged while it stayed open is invisible to every
other gate: the release gate inspects only issues closed **by** merged
pull requests, so a manually-closed issue — or one nothing ever closed —
never reaches it. Run this during the groom.

```bash
py - <<'EOF'
import json, re, subprocess

subjects = subprocess.run(
    ["git", "log", "--format=%s"], capture_output=True, text=True).stdout.splitlines()
print("commit subjects scanned: %d" % len(subjects))

reffed = set()
for s in subjects:
    reffed.update(re.findall(r"[(]#([0-9]+)[)]", s))
print("distinct issue numbers referenced: %d" % len(reffed))

raw = subprocess.run(
    ["gh", "issue", "list", "--state", "open", "--limit", "500", "--json", "number"],
    capture_output=True, text=True).stdout
open_now = {str(i["number"]) for i in json.loads(raw)}
print("open issues: %d" % len(open_now))

hits = sorted(reffed & open_now, key=int)
print("referenced by a merged commit and still open: %d" % len(hits))
for h in hits:
    print("  #%s" % h)
EOF
```

Pass condition: the check prints how many commit subjects it scanned, how
many issue numbers it found in them, and how many open issues it compared
against, before printing the hits. All three counts are load-bearing — a
sweep that reaches nothing and a sweep that finds nothing print the same
empty result otherwise. A scanned count of zero is a failure, not a clean
run.

Each hit is a decision, not a defect: the work may have merged under a
different issue, or the issue may name more than the commit closed. Close
it or record why it stays open. One instance stayed open across eleven
releases before this sweep existed.

## Release a new version

This repo has no version manifest (plain Markdown), so it follows the
no-build release variant from ADR-006: tag `main` directly via a GitHub
Release — there is no `chore: release` branch, commit, or PR.

1. Confirm the milestone's issues are all closed and `main` is green
   (`py tests/run_smoke.py` passes) and up to date (`git pull`)
2. Confirm the inverse — every issue closed since the previous tag
   carries the milestone being released. Step 1 reads the milestone
   and cannot see work merged without one. Run the milestone-coverage
   check in `templates/base/core/git.md`, setting its `MILESTONE` to the
   milestone being released. Left unset it reports that the check does
   not apply — correct for a routine release on a project that scopes
   some cuts and not others, and a silent pass here, where every cut is
   milestoned
3. Confirm nothing else is ready to merge, or decide which side of the
   tag it lands on. Run the release-ordering check in
   `templates/base/core/git.md` — anything merged between the release
   commit and the tag ships inside the release with no note naming it,
   and both pull requests stay green in either order
4. Cut `CHANGELOG.md` — reconcile the `Unreleased` section against the
   commits the release carries with the changelog-completeness check in
   `templates/base/core/git.md`, then rename that section to
   `## [A.B.C] - YYYY-MM-DD` and open an empty `Unreleased` above it.
   This repo has no version manifest to carry the cut, so it is its own
   pull request, and it MUST merge before the tag below — a tag placed
   first names a tree whose changelog does not mention the release.
   The check's two counts are not required to match: a commit touching
   no template carries no entry, so a journal or tooling change is
   expected to appear in the carried list with nothing answering it
5. Create and push the tag **annotated**, naming the commit it belongs
   to rather than whatever `main` points at — `tag-guard.yml` fails a
   pushed lightweight `v*` tag, and `gh release create` makes a
   lightweight one when the tag does not already exist:
   ```bash
   git tag -a vA.B.C <release-commit> -m "vA.B.C — <milestone theme>"
   git push origin vA.B.C
   ```
   Naming the commit is what keeps the journal step below true. Tagging
   `main` puts a journal or unrelated pull request merged in between
   inside the release, and nothing reports it
6. Cut the release from the existing tag with a bare-version title and
   auto-generated notes:
   ```bash
   gh release create vA.B.C --verify-tag --title vA.B.C --generate-notes
   ```
   `--verify-tag` aborts rather than creating the tag, so the release
   can only ever attach to the annotated tag pushed in step 5. Notes
   are built from the PRs merged since the previous tag. The title is
   the bare version and carries no theme — the annotated tag's message
   and the milestone's description both carry it already, and a release
   list mixing the two forms reads as two conventions rather than one
7. Close the `vA.B.C` milestone once the release is published
8. Record that the session owes a `docs/dev-journal.md` entry — do not
   write it here. The entry is written at the end-of-session audit item
   that owns it, which is the last item for a reason: it is the only one
   whose output is a record of the others, and items above it file
   issues and open pull requests. Written at this point instead, the
   entry names none of them, and `base-docs` fixes its account once
   written, so the repair is a second entry for one session. When the
   entry is written it is still **separate** — its own
   `docs(journal): ...` PR with **no milestone**, not part of the
   release. A release cut without a wrap-up still owes the entry;
   publishing the release does not discharge it
9. Verify the release exists before closing the session. This is last
   rather than part of step 6 on purpose: a check inside a step is
   skipped whenever the step is:
   ```bash
   gh release view vA.B.C --json tagName,name,isDraft --jq '.tagName, .name, .isDraft'
   ```
   Pass condition: prints the tag, the bare-version title, and `false`.
   `release not found` means step 6 did not happen — and every other
   artifact of the release, the tag and the closed milestone and the
   journal entry, is present either way, so nothing else surfaces it

Which of those steps are actually enforced, audited per step as
`quality-gates-procedure-steps` requires:

| Step | Enforced by |
| --- | --- |
| 1 | `py tests/run_smoke.py`, plus the milestone's own issue list |
| 2 | the milestone-coverage check in `base/core/git.md` |
| 3 | the release-ordering check in `base/core/git.md` |
| 4 | the changelog-completeness check in `base/core/git.md` |
| 5 | `tag-guard.yml`, which fails a pushed lightweight `v*` tag |
| 6 | step 9, and nothing before it |
| 7 | nothing — an open milestone after a published release is silent |
| 8 | nothing — a missing entry surfaces at the next wrap-up, or never. The entry itself is gated by the audit item that writes it |
| 9 | nothing; it is the closing check, so it is the one to run by hand |

Step 6 is the one to protect first, because its omission cannot be
repaired afterwards: publishing the release later dates it after the
release that followed it, and a mis-ordered release list is worse than a
visibly absent entry. `v2.57.0` is the instance — tagged, milestoned and
journalled, never published, and deliberately left absent for that
reason.

Projects with a version manifest (`package.json`, `pyproject.toml`,
etc.) instead follow the branch → bump → PR → merge → tag flow; see
ADR-006 and `base/core/git.md`.
