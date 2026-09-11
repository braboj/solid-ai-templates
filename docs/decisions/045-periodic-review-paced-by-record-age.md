---
id: "045"
status: Accepted
date: 2026-09-07
category: process
supersedes: ["033"]
superseded_by: []
---

# ADR-045: A periodic review is paced by the record's age

## Context

The pre-release sequence in `base-git` names a periodic project-wide
audit as its third step. The obligation was scoped to the releases that
move an interface: a minor or major release carried a current review, a
patch carried nothing. That scoping was a repair for a gate attached to
every release, where most releases were patches and the operator cleared
the step by writing a document declining the work.

The repair moved the problem rather than removing it, because release
frequency is not a property of the project's shape. A repository whose
releases are mostly minors owes a fresh review on almost every cut. This
repository is that case.

Measured on 2026-09-07, `docs/audits/` held six dated records, four of
them written within the preceding seven days — 2026-09-01, 2026-09-03,
2026-09-06 and 2026-09-07 — one per minor cut. A review whose subject is
the shape of the whole project has nothing new to read three days after
the last one. So the gate was again collecting an artifact rather than a
reading, and every signal available said it was working.

The prior decision considered a calendar cadence and rejected it, on the
grounds that it decouples the review from the changes it reads: a quiet
quarter would owe one and a busy one might not. The first half of that
holds. The second does not survive the on-demand events staying in
force.

A busy period reaches an audit through the events that make one worth
reading — a milestone closing, a major feature landing, a launch — long
before an interval expires. So the interval is never the thing that
schedules a review in a busy period. It only catches the project that
hits none of those events, which is the quiet case, and the quiet case is
the one a cadence is for.

## Decision

1. **Pace by the record's age** — where a project gates its release on a
   periodic project-wide audit, the obligation MUST be decided by the age
   of the newest record against a review interval the project declares:

   - not by the release kind
   - not by the release count

   A release whose newest record falls inside the interval owes nothing,
   whatever version it moves; a release whose newest record falls outside
   it owes a review, whatever version it moves.

2. **The interval is a floor, not the schedule** — the events that make
   a review worth reading trigger one on demand and remain the primary
   trigger. The interval exists to catch the project that reaches none of
   them.

3. **The figure is declared once** — the interval is stated beside the
   check that reads it, in the widest-reaching template that carries
   either, and every other place that lists the triggering events defers
   to it rather than restating a number.

4. **A project running no audit is exempt, an empty record set is not** —
   the check MUST treat:

   - a missing audit directory as the project not running a periodic
     review
   - a directory holding no dated record as a project that owes one and
     wrote none

5. **An unreadable value is a finding** — a value the gate cannot read
   and a value that exempts the release both mean the comparison does not
   run. Reading them alike turns a typo into a silent exemption, so the
   gate MUST refuse the value rather than skip on it.

6. **Re-scoping re-points the controls** — a change that moves what a
   gate evaluates MUST re-point that gate's negative controls in the same
   change and confirm each still fails. A fixture built to fire under the
   old scope stops firing the moment the scope moves, leaving the suite
   green while testing nothing.

## Alternatives considered

- **Keep the release-kind scoping** — rejected; it is the state that
  produced four whole-project reviews in seven days, and its decay looks
  like compliance from every angle the surrounding rules can see.
- **Drop the gate entirely, leaving the audit purely on demand** —
  rejected; nothing would then poll the obligation, and a deferral with
  no watcher reads exactly like a live obligation. A date is polled by
  every release, which is what lets it carry the obligation.
- **Scope by accumulated change rather than time** — rejected for the
  reason the prior decision rejected diff-based scoping. Deciding
  whether a body of change can move a project-wide review is the
  judgement the review itself makes, so the gate would need the review's
  answer to decide whether to ask for it.
- **Keep the release-kind scoping and add an interval on top** —
  rejected; two triggers for one artifact means the stricter one always
  decides, so the interval would change nothing while doubling what the
  rule has to explain.

## Consequences

- `templates/base/core/git.md` states the pacing rule and carries the
  `periodic-review-scope` check, which no longer reads a release version.
  Pre-release step 3 changes with it; the enforcement-table row does not,
  the step still being conditional on the project running an audit.
- `templates/base/workflow/360.md` drops the quarterly bullet from its
  trigger list and defers to the declared interval, so the figure exists
  in one place.
- The check becomes runnable in this repository rather than reporting as
  not applicable, because it takes no parameter that only a release sets.
  Its conformance disposition scores two counts and a zero exit.
- A project releasing several times a week produces one review per
  interval instead of one per minor, and stops writing decline records
  for releases whose record is already current.

## Related

The currency comparison the check performs, and the non-strict rule it
follows, are stated in `base-git` beside it.
