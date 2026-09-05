# Base — Scope Guard

[ID: base-scope]

## Purpose

Prevent scope creep during agent-assisted work sessions. Agents tend to
agree with expansions rather than pushing back, leading to sessions that
start with one task and end with five unrelated changes — none fully
finished.

## Session startup

Before starting any work, the agent MUST:

1. Read all documents referenced in the project's CLAUDE.md (e.g.
   `docs/solid-ai-templates/templates/base/core/git.md`,
   `templates/base/core/docs.md`, etc.)
2. Apply the project's adopted conventions. Reading or updating a template
   does not adopt its new rules; follow "Adopting shared rules" in
   `templates/base/core/docs.md`
3. Check which branch you are on — if not `main`, ask why before
   proceeding
4. Check `git status` and preserve existing work. Continue independent work
   when possible; ask only if overlapping changes prevent safe progress.
   Uncommitted changes do not authorize committing, pushing, or merging them.
5. Clean up stale branches: `git fetch --prune` to remove stale
   remote-tracking refs, then delete local branches whose PRs have
   merged. Verify each against the PR record, never against
   `git branch --merged` — a squash merge writes a new commit that
   the branch tip is not an ancestor of, so the filter matches
   nothing and exits 0, which is indistinguishable from "nothing to
   clean". When the PR is merged but its head no longer matches the
   local tip, the remote head was rewritten (safe) or the branch
   holds unpushed commits (not safe): inspect the difference rather
   than assuming either. Concrete commands belong in the platform
   template.
6. Check deploy health — verify the latest CI/CD deploy on `main`
   completed successfully; flag if stuck, failed, or pending. A deploy
   can sit broken for hours unnoticed when startup checks only cover
   branch and status. Concrete commands belong in the platform template.
7. Confirm the scope with the user before making changes
8. If the task is ambiguous, ask: "What is the specific deliverable for
   this session?"
9. Write down the agreed scope — refer back to it when the session
   drifts
10. Review open issues related to the agreed scope before writing code

## Mandatory startup block

Every project CLAUDE.md MUST include a prominent startup block at the
top of the file listing all referenced template files with an explicit
instruction to read them before the first response. This applies to both
reference mode and hybrid mode.

The startup block MUST:

- Appear before section 1 (Project)
- List every template file the project depends on, resolved on BOTH
  axes. A stack chain and a platform template are selected
  independently: no stack declares a platform dependency, because the
  platform follows from where the repository is hosted rather than
  from what the project is built with. Walking the stack's
  `DEPENDS ON` graph therefore terminates cleanly, yields no platform
  template at all, and shows nothing to say one is missing. The block
  MUST name:
  - the resolved chain for the project's stack
  - exactly one platform template, for the host the repository lives
    on
  - any base template the project adds deliberately, outside either
    axis
- Check — the block names exactly one platform template. Pass
  condition: the command prints `1`. Zero means the second axis was
  never resolved, which is the common failure and is invisible in the
  block itself:

  ```bash
  grep -oE 'platform/[a-z-]+[.]md' CLAUDE.md | sort -u | wc -l
  ```

  A project whose context file inlines its rules rather than
  referencing them has no list to check; the two-axis requirement
  still governs which templates were read to produce it
- Use imperative language: "You MUST read every file listed below IN
  FULL using the Read tool before you respond"
- State the consequence: "If you respond without reading them, you are
  violating project rules"

This requirement exists because `templates/base/workflow/scope.md` says "read
all documents
referenced in CLAUDE.md" — but `scope.md` is one of the files that needs
to be read first. The startup block breaks this chicken-and-egg problem
by placing the instruction directly in CLAUDE.md, the one file that is
always loaded into context automatically.

## During work

- If a task grows beyond the original scope, flag it explicitly:
  "This is expanding beyond the original task — should I continue or
  finish the current work first?"
- Do not silently absorb new requests into the current work stream
- Finishing and committing the current work SHOULD take priority over
  starting something new
- Build after every change — do not accumulate multiple changes without
  verifying the build still passes

## Tooling-produced scope creep is silent — revert and file

Scope creep from a new user request is loud and easy to catch. Scope
creep from tooling is silent: a script run as part of a focused change
produces more output than the scope requires, and the extra changes
look like part of the work.

- When a bulk regenerator rewrites N unrelated entries, a formatter
  touches unrelated files, or a code generator updates unaffected
  modules, revert the unintended changes from the working tree before
  committing
- File the drift as a separate issue and address it under its own
  scope — bundling it ships a multi-X change disguised as a single-X
  change and hides the drift behind the PR title
- This does not apply to intentional bulk operations — a "refresh all
  logs" PR is correctly bulk by intent

## Reconcile candidates against scope before planning

A suggestion for what to do next — an audit's feature recommendation, a
session-handoff or memory breadcrumb, a "showcase value" idea — is a
candidate, not a decision. Reconcile it against the authoritative record
before it becomes planned work:

- An audit or feature recommendation MUST be checked against the
  documented scope (the in/out-of-scope list — e.g. arc42 §3.3 — and the
  requirements). A candidate that falls in "Out of scope" is dropped, or
  promoted by a deliberate scope-changing ADR — never slipped in because
  it sounds valuable. "Best practice" does not override a written
  boundary; a planned item not traceable to an in-scope requirement or a
  scope-changing ADR is scope creep.
- A handoff breadcrumb names continuity, not priority. A
  "next: continue on X" pointer marks the cheapest resumption of the last
  thread, not the highest-priority move. Before acting, re-check X's
  priority — and its milestone, where the project uses milestones —
  against what the project is currently working on; if they differ, ask
  first. The wrap-up writer MUST validate each candidate against the
  tracker before listing it (`gh issue view <N>` or equivalent — still
  open, not blocked, and not in a milestone the project has moved past),
  drop closed candidates, and record each surviving pointer's priority
  (and milestone, if any) inline so the next session sees any mismatch.
  An issue with no milestone MUST NOT be dropped on that basis — an empty
  milestone carries no scheduling signal either way. A breadcrumb is
  captured from session memory, not synced from the tracker, so a stale
  entry burns the next session's setup time on already-done work.

## Default scope boundaries

- One logical unit of work per session (one feature, one chapter, one
  component, one bug fix)
- Changes that support the current unit (tests, docs, formatting) are
  in scope
- Restructuring unrelated code, creating new projects, or adding
  infrastructure is out of scope unless explicitly requested

## When in doubt

- Finish the current task
- Commit the current work
- Then ask whether to start the new task

## Scope expansion protocol

When the user requests something out of scope:

1. Acknowledge the request
2. State what the current scope is
3. Ask: "Should I finish the current work first, or switch to this?"
4. If switching, commit current progress before starting the new task

## End of session audit

When the user signals end of session ("wrap up", "let's finish",
"end session", "close out", or similar), the agent MUST print the full
checklist below and execute each item sequentially. Mark each item done
(with result) before moving to the next. Do not batch, skip, or
summarize — visible sequential execution prevents missed steps.

1. **Commits and push** — all changes committed and pushed (via PR if
   branch-protected)
2. **Close issues** — reconcile the open-issue list against the work
   shipped this session, from the tracker rather than memory, and close
   what is done (verify auto-close worked)
3. **Epic checklists** — update epic checklists if relevant
4. **ADRs** — apply the decision threshold in
   `templates/base/core/docs.md`. Routine moves, naming, and compliance
   repairs need no ADR; one coherent architectural choice may span PRs.
5. **CLAUDE.md** — for each new convention/rule, apply the doc-placement
   decision tree in `ai-workflow.md` (Doc placement decision tree
   section): evaluate code → ADR → README → PLAYBOOK → CLAUDE.md →
   memory in order. CLAUDE.md is the home ONLY if the agent MUST
   apply the rule on every turn.

   CLAUDE.md contains rules only — not changelogs, package architecture,
   per-feature progress, or session logs. Keep rules concise without
   removing necessary qualifiers; paragraph length does not require an ADR.
6. **README.md** — for each new command, dependency, or structural
   change, is it reflected? Name the section.
7. **ONBOARDING.md** — ensure `docs/ONBOARDING.md` exists and covers
   each new tool, prerequisite, or setup step. Create it if missing;
   name the section. A missing doc is work to do here, not a gap to
   report.
8. **PLAYBOOK.md** — ensure `docs/PLAYBOOK.md` exists and covers each
   new command, script, or workflow added. Create it if missing; name
   the section. A missing doc is work to do here, not a gap to report.
9. **Submodules** — review updates needed for the current task or a material
   security risk. A newer template tag alone creates no update obligation;
   follow the project's adoption policy before changing a pin.
10. **Template feedback** — propose upstream work for a demonstrated shared
    defect or recurring need. Check existing issues first. A reusable-looking
    preference alone requires no issue, ADR, or `Upstream:` bookkeeping;
    contribute when the user has authorized that work.
11. **Flag gaps** — if any item cannot be completed this session, report
    it as pending (never as done) before closing — including deferred
    cross-repo work, such as an upstream contribution that was flagged
    but not yet landed. Reserve "pending" for work that is genuinely
    blocked — it needs a decision, a credential, or the user. Work the
    agent could do but has not done is not pending; do it.
12. **Dev journal** — add a session entry to `docs/dev-journal.md`
    (date, tool, key changes, PRs merged, issues closed/created). This
    item sits after flagging gaps because it is the only one whose output
    is a record of the others, and flagging a gap resolves into a change
    whenever the fix is small enough to apply on the spot — which is when
    a wrap-up should apply one. Written earlier, its merged-pull-request,
    issue and upstream lines are incomplete by construction, and an
    entry's account is fixed once written, so the correction costs a
    second entry for one session
    - Where the checklist runs more than once in a session — a release
      wrap-up, then a close-out — only the last pass writes the entry.
      An earlier pass records that the session owes one. The entry is
      owed by the session and discharged once, at the end
13. **Summary** — summarize what was done and what's next
