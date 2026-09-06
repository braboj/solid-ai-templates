---
id: "042"
status: Accepted
date: 2026-09-06
category: process
supersedes: []
superseded_by: []
---

# ADR-042: A tag push runs the release gates

## Context

Four of the checks the base tier ships are parameterised by the release
being prepared: the milestone the release is scoped to, and the version
itself. The parameterisation is deliberate and correct. Nothing in a
repository's state distinguishes a release commit from an ordinary one —
an untagged HEAD means only that a commit has landed since the last tag,
which is the ordinary condition of a repository between releases. A
detector reading it as the release moment reports the failure shape on
almost every day, and a check whose ordinary output is its defect output
trains its reader to skip it.

The cost was that the constant is set by editing the check. Measured on
the tree at the time of this record, 14 of 53 registered check blocks
produced an automatic verdict in continuous integration; the release
gates were the largest group that did not, reporting that they did not
apply on every run. They are also the checks whose omission is least
recoverable, and the ones that only ever ran when somebody remembered.
Four consecutive minor releases shipped owing a periodic review, under a
check that existed and was correct throughout.

A tag push is the one repository event that does say a release is
happening. Reading the version from it removes the guess without
loosening anything: the check still refuses to run when no release is
declared, and the tag is a declaration.

One obstacle was not visible until the gates were run at a tag. Each
resolves the release it follows with the newest reachable tag, which on
the release commit is the previous release and at the tag itself is the
tag being released. The range is then empty and the check compares
nothing — the state a check must refuse rather than pass.

## Decision

1. Each release gate MUST read its parameter from the environment,
   falling back to the empty value that reports the check does not
   apply. Setting the constant by hand remains supported; the
   environment is a second answer to the same question, not a
   replacement.
2. A tag push MUST run the release gates, with the version taken from
   the tag and the milestone resolved from it by its
   `v<major>.<minor>` prefix. A release scoped to no milestone leaves
   the parameter unset, and the check reports that it does not apply.
3. The same workflow MUST be dispatchable with the version as an input,
   so the gates can be run at the release commit, where they can still
   refuse rather than report.
4. A gate resolving the release it follows MUST resolve it from the
   commit under release. Where a tag points at HEAD, the baseline is the
   tag before it.

## Alternatives considered

**Leave the gates manual and state the cost in the runbook.** This is
what the acceptance criteria offered as the alternative, and it is
honest: the operator would read that the step is theirs. It was rejected
because the evidence is that the step is skipped rather than declined,
and a runbook line does not distinguish the two afterwards.

**Run the gates on every push, detecting the release moment.** Rejected
for the reason the parameterisation exists: no state distinguishes the
moment, so the detector reports the failure shape on almost every day.

**Dispatch only, with no tag trigger.** Strictly better than editing a
constant, and still requires somebody to remember — which is the failure
being addressed. Kept as the second trigger rather than the only one.

**Gate the tag itself, refusing the push.** A tag push cannot be
rejected by a workflow, and a tag on a public repository cannot be taken
back cleanly. The prevention half is what the dispatch trigger and the
runbook step carry.

## Consequences

- The release gates execute on every release, whether or not anyone
  remembers. What they catch on the tag push is reported rather than
  prevented, which is the residual cost of triggering after the
  irreversible step.
- Two of the gates reach a reading rather than a verdict when they run,
  so both are registered in the reading budget with the reason. A tag
  push therefore produces readings that a routine push does not.
- The runbook keeps its manual step. It is now the prevention half
  rather than the only execution, and running it early costs nothing
  that the automatic run repeats.
- Correcting the baseline changes what the gates measure on the release
  commit too: previously the newest tag, now the tag before whichever
  one points at HEAD. On an untagged HEAD the two are the same.
