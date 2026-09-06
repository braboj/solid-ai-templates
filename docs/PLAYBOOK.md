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
   # how many of the 37 roots resolve a candidate file?
   for s in $(py tools/resolve.py --roots); do
     py tools/resolve.py "$s" | grep -q 'core/review.md' && echo "$s"
   done | wc -l
   ```

   `--roots` and not `--list`: a project resolves its stack, then its
   extras, then its platform, each as its own root, so the stacks are
   only part of what carries a file. Measuring over `--list` counts the
   stack chains and silently omits every opt-in root.

   A **chain template** carries rules the generated project follows.
   Reach is the criterion for it, and a rule in one that no root
   resolves reaches no generated context file.

   An **opt-in template** is a root of its own. Its reach is 1 — itself —
   and that is the point rather than a low score: what it may rely on is
   the core tier plus its own `depends_on` tree, because the stack it is
   paired with is unknown when it is authored. `platform/` templates are
   the clearest case, since a project picks one regardless of stack.

   A **pipeline template** carries rules about generating or consuming a
   context file, and `templates/INTERVIEW.md` reads it directly rather
   than any root resolving it into a project. Reach says nothing about
   whether the rule lands: `base/core/agents.md` is carried by a single
   root — its own — and shapes every file the pipeline generates.
   Recognise one by asking what reads it: a stack, an opt-in root, or
   INTERVIEW.md.

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

Use this workflow only after applying the decision threshold in
`templates/base/core/docs.md`. Routine naming, directory moves, and policy
repairs need no ADR. One coherent architectural decision may cover related
work across several issues or PRs. ADRs live in `docs/decisions/`; ADR-010
records the frontmatter schema.

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
   list. Preserve historical claims; format-only changes are also allowed
   under the decision-log rules in `templates/base/core/docs.md`.
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
8. Open the PR. Preserve the merged decision as history. Routine later
   refinements update current docs and the PR; only a material architectural
   replacement needs a superseding ADR.

## Adopt a template policy update

A newer tag alone creates no work. Review a template update for a named project
need or material risk, applying "Adopting shared rules" in
`templates/base/core/docs.md`. Keep existing adopted conventions until the
project deliberately changes them; declining a candidate needs no ADR or ticket.

For consumers adopting the selective-adoption and ADR-threshold update:

- Inline the adoption boundary in the root context file before applying newly
  read template rules. Update copied inline rules as well as the submodule pin.
- Replace old directory-move, paragraph-length, and per-issue ADR triggers in
  the local context, wrap-up checklist, and authoring instructions.
- Keep existing ADRs as history. Put routine refinements in current docs and
  the PR; do not create a consolidation project or a decline register.
- Reconcile the reference list if a chosen update changes dependencies, and
  run the project's relevant existing checks. Select a released tag when the
  policy ships; until then the current pin remains usable.

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

Prompt sizes and the minimum context window per stack category are in
README's "Model limitations" section, generated from the resolved
chains by `py tools/sync.py`. A copy here would be a second set of
figures with no generator behind it, and the copy is what ages.

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

   A rule added to a widely resolved file is read by every project on
   every chain carrying it, on every turn, and nothing refuses that
   size. `README.md`'s model-limits table reports it per stack
   category beside the smallest context window that still holds it, and
   `py tools/sync.py --check` fails when the table drifts from the
   tree. Read the table's diff before merging, and say in the pull
   request what the addition is worth.

   A category crossing to a larger window is a change to what a consumer
   needs to run the stack at all, and that is refused rather than
   reported: SYS-16 fails until the new tier is recorded in
   `tests/context-tiers.txt` in the same change.

   Before adding a paragraph, try stating the rule inside the one that
   already carries the narrow version of it. A widened rule folded in
   place is often shorter than the text it replaces: the
   release-proposal record went from +472 characters as its own
   paragraph to 98 characters shorter than the narrow rule it replaced.
   Measured 2026-09-03 on `base/core/git.md`.

3. **Agent check**: attach `INTERVIEW.md` + the changed template to an agent
   and review the output for coherence; or run the
   relevant E2E test if one exists:
   ```bash
   py tests/run_e2e.py STK-01   # example — replace with the relevant ID
   ```
   Reports are written to `tests/reports/` after every run.

---

## Audit redundancy

A rule stated in two active sections of the same resolved chain dilutes
the agent's attention (see `docs/design/template-content-quality.md`). The
audit scans every root a project can pick -- the stacks and the
orthogonal templates alike -- and reports duplicates, excluding those the
override model legitimately produces (one section `[OVERRIDE]`s the
other):

```bash
py tools/audit_redundancy.py           # exact in-chain duplicates
py tools/audit_redundancy.py --near    # also paraphrase near-duplicates
py tools/audit_redundancy.py --check   # exit 1 if any exact duplicate
```

`--check` gates the exact tier only and prints the near count beside
its verdict, so a passing run states what it did not gate (ADR-038).
A near pair cannot fail CI; the count is what makes it visible.

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
py tests/run_conformance.py        # the templates' own checks, run here
py tests/run_conformance.py --list # dispositions only, run nothing
py tests/run_e2e.py                # canary test (python-lib)
py tests/run_e2e.py --all          # all agent tests
py tests/run_e2e.py STK-01 FMT-01  # specific tests only
py tests/run_e2e.py --dry-run      # build prompts, skip agent calls
```

See `tests/CODIFICATION.md` for the ID scheme and `tests/INDEX.md` for the
full list of specs. Requires `py -m pip install pyyaml` for the manifest
check.

`run_smoke.py` prints what each check inspected under its verdict — the
files scanned, the chains resolved, the directives compared. Those lines are
not findings; read them when a count moves without the tree moving, which is
how a check that silently stopped reaching its corpus shows up. A count of
zero fails the check, and a check that passes while reporting nothing is
failed by the runner itself.

`run_smoke.py` checks that the templates COMPOSE. `run_conformance.py`
checks that this repository OBEYS them — it extracts every fenced check in
`templates/` and either runs it here or records why it does not apply.
Adding a fenced check to a template without a disposition in
`tests/conformance.py` fails the run, which is what stops a new check from
arriving unexamined. Checks reaching GitHub need `gh` authenticated.

A check whose verdict is a judgement reports `REVIEW` rather than `PASS`,
and the summary counts it as awaiting a reading. It does not fail the run
— the exit status answers whether a verdict was reached and was negative —
so a run ending `0 failed  2 not applicable  6 awaiting a reading` is not
a clean run until someone has read those six. The middle count is not
among them: a check whose moment is not in progress exits 3 and has
answered, which is why it is counted apart. That is different from a
`SKIP`, which a person decided in advance about this repository and which
runs nothing at all. Recording them as passes is what let four
over-long changelog entries sit inside a green report for two sessions.

A check only earns that status where nothing in its output can be decided.
The changelog bound declares a limit and counts against it, so it is a
scored verdict now, and each check that stays a judgement carries a
`reason` in `tests/conformance.py` naming what about it takes a person.
The runner refuses a judgement disposition that states none.

Which checks may reach that status is fixed in `tests/reading-budget.txt`,
one title per line above the reason it cannot reach a verdict. A reading
the file does not name fails the run, so the set grows only in a diff that
says why; a named check that reaches a verdict or reports it does not apply
passes freely, which is what keeps the release moment from failing the run
— the ordering check answers "does not apply" while HEAD is the tag. An
empty budget is refused rather than obeyed. On a hosted runner the summary
is written to the run summary as well as the log.

Adding a judgement disposition therefore means two edits in the same
change: the `reason` beside the disposition, and the title in the budget.
Renaming a check means moving its budget line too — the runner reports the
stale entry as an unbudgeted reading rather than ignoring it.

---

## Control-test a check you are changing

A check that stopped reporting a finding and a check that can no longer
report one produce the same clean result. Before believing a narrowed or
newly-forked check, drive it through a fixture that MUST be reported and
one that must not.

Where the fixture can live outside `templates/`, write it, run the single
check by a string from its body, and delete it:

```bash
py tests/run_conformance.py "<string from the check body>"
```

Where the fixture must live UNDER `templates/` — anything the check scans
by walking that tree — the runner refuses to execute: an unregistered
fenced block in the fixture is a missing disposition, which it reports
before running anything. Call its extraction directly instead, which skips
the registry reconciliation:

```bash
py - <<'EOF'
import sys, tempfile
sys.path.insert(0, "tests")
from run_conformance import iter_blocks, run_block

body = next(b[3] for b in iter_blocks()
            if b[0] == "base/core/docs.md" and any("<find>" in l for l in b[3]))
code, out = run_block(body, "bash", tempfile.mkdtemp())
print("exit %d" % code)
for line in out:
    print("  " + line)
EOF
```

Pass condition: the fixture that must be reported is reported, the one
that must not is not, and the check's own corpus counts move between the
two runs. `testing-control-corpus-moves` in
`templates/base/core/testing.md` is the rule, and says why the third is
what makes the first two readable.

For a check that takes an argument — a milestone, a module, a field —
replace the placeholder line in `body` before calling `run_block`. The
placeholder is not always what the issue or the prose calls it:
`MILESTONE = None` rather than an empty string cost a first attempt here.

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
dimensions). Run one before a minor or major release, after a milestone, or
quarterly. A patch release owes neither the audit nor a record
declining it.

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
6. Merge with the default squash subject — `gh pr merge <number>
   --squash`, with no `--subject`. GitHub composes that subject from
   the title and appends the pull request number; supplying one
   replaces both. The milestone-coverage gate reads those numbers
   back out of the log, so a hand-typed subject removes the reference
   it resolves, and the gate reports on the commits it can still read
7. After merge: delete the branch and pull `main`

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

`tools/resolve.py --check` is a real gate and a narrower one: it compares
`generated/` alone, prints the stale chains and exits `1`. CI runs it as a
required step and every file in `generated/` opens with a banner naming it.
The gate above subsumes it, so this step still runs one command — and an
unknown flag on that tool exits `1`, so a typo there cannot read as a
clean gate.

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
   the measurement found and its date. Measure it with the extractor the
   check itself uses, not one written for the measurement: a looser scan
   counts occurrences the check never sees — a directive quoted inside a
   fenced block, a name in prose — and the plan is then sized against a
   corpus nothing acts on
3. **Read the whole issue before judging whether it earns its change.** A
   ticket's measurements, its reach analysis and the data it carries from a
   consuming project sit below its opening paragraphs, so a verdict formed
   from the first screen is formed from the part that argues least. Measured
   2026-09-01: four tickets were dispositioned as low-value from their first
   380 characters and all four verdicts were wrong — one carried 22 measured
   breaches across 13 of 16 records in a consumer repository, another
   reproduced a gate exiting zero over a deleted marker
4. Cluster by target file. Issues touching one section are one pull
   request rather than several, and the clustering is visible only once
   the claims are verified — two issues can name the same file and want
   changes that do not compose
5. Scope the cut from the clusters, then create the milestone. A theme
   falls out of what the groom found; choosing a theme first selects
   issues to fit it. The title is `vA.B.C — <theme>` and the description
   enumerates the issues; the release tag message quotes that theme, so
   a milestone titled with a bare version leaves the tag with nothing to
   quote
6. Assign the issues to it, and read the milestone's open count back.
   Creating a milestone and assigning its issues are two calls, and a
   milestone whose description enumerates five issues while holding none
   reads as scoped from every view that shows the title. Nothing else
   catches it: the release gate reads the issues a milestone holds, so an
   empty one passes

Grooming produces annotations, closures and a milestone, not scope edits.
An issue whose measurement shows it is narrower, wider or wrong as filed is
annotated with that finding and left open — restating the scope is the
implementer's step, and `base-review` covers the shapes it takes.

The one edit a groom is uniquely placed to make is a closure. An issue
whose premise a merged change has already settled has nothing left to
implement, and annotating it leaves the note waiting for an implementer who
will never come. The two are told apart by what the measurement found: the
claim moved and the work exists in changed form, so annotate; or the
premise was answered, so close with the evidence. Seven such closures have
happened across two grooms while this paragraph read as forbidding them.

Where a milestone already exists but its theme describes work that has not
happened, renumber it rather than dissolving it. A scoped milestone carries
an ordering and a rationale that took a groom to produce, and emptying it to
reuse the version number discards both. Move it to the next version, create
the version being cut under a theme matching what actually shipped, and
assign the closed issues to that. Met on 2026-09-03: `v2.73` was themed for
six unstarted issues while five unrelated ones had already merged, and one
issue had been put in it solely to satisfy the release gate.

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
no-build release variant from ADR-006. What that variant removes is the
version-bump commit and the `chore: release` branch carrying it — there is
no manifest to bump, so nothing needs one. It does not remove every pull
request: the changelog cut at step 4 is its own, and it is the release
commit the tag names.

Run `base/core/git.md`'s pre-release checks first — that sequence is the
source, and the nine steps below are this repository's release procedure
proper, not a restatement of it. Two of those checks bind here and neither
has a step below: the periodic-review-scope check, which a minor or major
release owes and a patch does not (set its `RELEASE` to the version being
cut; this repository keeps its records in `docs/audits/`), and the
pipeline-history check.

Read each gate's output, not its exit status. Most of these checks state
their pass condition as "prints nothing after the counts" and then print
findings without exiting non-zero, so a run that reports a real problem
still exits `0`. Measured during the `v2.77.0` cut: milestone-coverage
printed `a subject names closed issue 1456, which carries no milestone`
and exited `0`. An operator reading the status alone ships the defect the
gate just named.

Each gate below reads its parameter from the environment as well as from
the constant, so `RELEASE=v2.83.0 py tests/run_conformance.py` runs the
whole set in one pass without editing a template. The `Release gates`
workflow does exactly that on every tag push, resolving the milestone
from the tag's `v<major>.<minor>` prefix, and can be dispatched with the
version as an input to run them at the release commit.

That automatic run is the backstop, not the mechanism. It happens after
the tag, which cannot be taken back cleanly, so it reports what the steps
below exist to prevent. Run them here anyway.

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
   `templates/base/core/git.md`, setting its `RELEASE` to the version
   being cut. Left empty it reports that no release is in preparation and
   does not apply, which is correct on any ordinary day and a silent pass
   here. Then rename that section to
   `## [A.B.C] - YYYY-MM-DD` and open an empty `Unreleased` above it.
   This repo has no version manifest to carry the cut, so it is its own
   pull request, and it MUST merge before the tag below — a tag placed
   first names a tree whose changelog does not mention the release. That
   pull request's body is this repository's release proposal: it names
   every step of `base/core/git.md`'s pre-release sequence and the result
   it produced, including the checks that carry no step number here.
   The check's two counts are not required to match: a commit touching
   no template carries no entry, so a journal or tooling change is
   expected to appear in the carried list with nothing answering it
5. Tag and push, per `base/core/git.md`'s no-build sequence — the tag
   is annotated and names a commit, and that commit is step 4's
   changelog cut, not `main`. The theme in the tag message is the
   milestone's, which is where this repository keeps it
6. Publish the release from that tag, per the same sequence. Locally
   `tag-guard.yml` is what fails a lightweight tag, so the guard the
   sequence prescribes is enforced here rather than merely advised
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

The pre-release checks above the table are enforced by `base/core/git.md`
rather than by a row here, which is why they carry no step number: a
number would claim they are part of this sequence and drift from the one
that owns them. What keeps them from being skipped is not a number but
the record at step 4 — a check nobody ran is a line the release proposal
does not carry. Four minor cuts shipped before that record was required,
each owing a periodic review; ADR-037 holds their disposition.

Step 6 is the one to protect first, because its omission cannot be
repaired afterwards: publishing the release later dates it after the
release that followed it, and a mis-ordered release list is worse than a
visibly absent entry. `v2.57.0` is the instance — tagged, milestoned and
journalled, never published, and deliberately left absent for that
reason.

Projects with a version manifest (`package.json`, `pyproject.toml`,
etc.) instead follow the branch → bump → PR → merge → tag flow; see
ADR-006 and `base/core/git.md`.
