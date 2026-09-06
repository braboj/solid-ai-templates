---
id: "040"
status: Accepted
date: 2026-09-06
category: tooling
supersedes: []
superseded_by: []
---

# ADR-040: A reading is budgeted, not scored or silenced

## Context

`tests/run_conformance.py` reports a check as awaiting a reading when its
disposition reaches no automatic verdict. A reading is not a failure, so
the runner exits zero over one, and that is deliberate: scoring a
governance signal fails every conforming change, and this repository's own
rules oblige the change that trips one of them.

The consequence is that nothing registers when the set grows. On the CI
run measured at the time of filing the summary said `5 awaiting a reading`
and the job was green. A prior audit had recorded the number as 3. Nobody
had decided to accept two more; the count simply moved, in changes whose
diffs said nothing about it, and every run in between reported success.

That is the shape the readings were introduced to prevent — a number that
establishes nothing being taken as a pass — arriving through the runner
that reports them.

Two properties make a plain count the wrong instrument. The set moves with
the release moment: a check about ordering a release answers that it does
not apply while HEAD is the tag and produces a reading the day after, with
nothing decided in between. And the same run reports different totals on a
developer machine and a hosted runner, because two of the checks answer
about whether work is committed.

## Decision

The checks allowed to await a reading are named in `tests/reading-budget.txt`,
one title per line, each above the reason it cannot reach a verdict. The
conformance runner compares the run against that file:

- A check awaiting a reading whose title the file does not name fails the
  run. Growth arrives in the diff that causes it, beside the reason it was
  accepted, and a reviewer sees the addition rather than a moved total.
- A named check that reaches a verdict, or reports that it does not apply,
  passes freely. Shrinking is the direction the file exists to encourage,
  and it is what keeps the release moment from failing the run.
- A budget that reads empty is refused rather than obeyed. An empty file
  licenses every reading, which is the state the check exists to prevent,
  and a truncated read is indistinguishable from a deliberate one.
- Where the runner is hosted, the summary is written to the run summary as
  well as the log, so the readings are legible without opening a log a
  green job invites nobody to read.

The count itself remains a reading: it is reported, and reaching zero is
not required.

## Alternatives considered

**Fail the run on any reading.** This is scoring a governance signal, which
the quality tier already rules out: a rule obliging a registration edit for
each new check makes every conforming change trip a gate that scores
registration edits. It would also delete the distinction between a check
that cannot be automated and one that has not been.

**Annotate the run and change nothing else.** An annotation is visible and
carries no verdict, so the set can still grow silently — it moves the same
unread number to a more prominent place. Adopted as a component of the
decision above rather than as the whole of it.

**Track the count as a single frozen number**, the way the chain ceiling
tracks chain size. A number is the wrong instrument here: the set moves
with the release moment and with whether the tree is clean, so a single
figure would fail runs in which nothing changed, and a figure that
tolerated that movement would tolerate a substitution — one check reaching
a verdict while another stops reaching one, at a constant total.

## Consequences

- Adding a check whose disposition is a judgement now requires naming it in
  the budget with the reason, in the same change. That is the intended
  friction: the reason is what a later reader needs to decide whether the
  judgement is still warranted.
- The budget is a second place a check's title appears. A rename must move
  both, and the runner reports the stale entry as an unbudgeted reading on
  the next run rather than silently ignoring it.
- The file records only what a reading costs to leave unautomated. It says
  nothing about whether the reading was read, which remains a matter of
  procedure.
