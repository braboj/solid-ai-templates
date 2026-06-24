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
   `docs/solid-ai-templates/templates/base/core/git.md`, `templates/base/core/docs.md`, etc.)
2. These contain binding conventions that CLAUDE.md inherits — do not
   proceed until you have read and understood them
3. Check which branch you are on — if not `main`, ask why before
   proceeding
4. Check `git status` — if uncommitted changes exist, resolve before
   starting new work
5. Clean up stale branches: `git fetch --prune` to remove stale
   remote-tracking refs, then `git branch --merged main | grep -v
   main | xargs -r git branch -d` to delete local branches whose
   PRs have squash-merged
6. Confirm the scope with the user before making changes
7. If the task is ambiguous, ask: "What is the specific deliverable for
   this session?"
8. Write down the agreed scope — refer back to it when the session
   drifts
9. Review open issues related to the agreed scope before writing code

## Mandatory startup block

Every project CLAUDE.md MUST include a prominent startup block at the
top of the file listing all referenced template files with an explicit
instruction to read them before the first response. This applies to both
reference mode and hybrid mode.

The startup block MUST:

- Appear before section 1 (Project)
- List every template file the project depends on
- Use imperative language: "You MUST read every file listed below IN
  FULL using the Read tool before you respond"
- State the consequence: "If you respond without reading them, you are
  violating project rules"

This requirement exists because `templates/base/workflow/scope.md` says "read all documents
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
2. **Close issues** — close completed issues (verify auto-close worked)
3. **Epic checklists** — update epic checklists if relevant
4. **Dev journal** — add a session entry to `docs/dev-journal.md`
   (date, tool, key changes, PRs merged, issues closed/created)
5. **ADRs** — record any architectural decisions in `docs/decisions/`.
   Check: were any new directories created or content moved between
   documents? Each one needs an ADR.
6. **CLAUDE.md** — for each new convention/rule, apply the doc-placement
   decision tree in `ai-workflow.md` (Doc placement decision tree
   section): evaluate code → ADR → README → PLAYBOOK → CLAUDE.md →
   memory in order. CLAUDE.md is the home ONLY if the agent MUST
   apply the rule on every turn.

   CLAUDE.md contains rules only — not changelogs, package architecture,
   per-feature progress, or session logs. Each rule fits on one line;
   if it needs a paragraph, write an ADR and leave a one-line pointer
   here. Evaluate items individually; do not batch-dismiss.
7. **README.md** — for each new command, dependency, or structural
   change, is it reflected? Name the section.
8. **ONBOARDING.md** — for each new tool, prerequisite, or setup step,
   is it documented in `docs/ONBOARDING.md`? Name the section.
9. **PLAYBOOK.md** — for each new command, script, or workflow added,
   is it documented in `docs/PLAYBOOK.md`? Name the section.
10. **Submodules** — check if upstream submodules need updates
    (`git submodule update --remote`); commit the pointer bump if needed
11. **Template feedback** — for each new pattern or convention
    introduced, state whether it is project-specific or reusable. If
    reusable, name the upstream template file and file an issue on the
    upstream repo (not a downstream note) — naming a candidate is not
    contributing it
12. **Flag gaps** — if any item cannot be completed this session, report
    it as pending (never as done) before closing — including deferred
    cross-repo work, such as an upstream contribution that was flagged
    but not yet landed
13. **Summary** — summarize what was done and what's next
