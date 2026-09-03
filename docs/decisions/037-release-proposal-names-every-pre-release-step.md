---
id: "037"
status: Accepted
date: 2026-09-03
category: process
supersedes: []
superseded_by: []
---

# ADR-037: The release proposal names every pre-release step

## Context

`base/core/git.md` carries an eight-step pre-release sequence and names the
checks that enforce it. This repository's `PLAYBOOK.md` release procedure
defers to that sequence in prose and then gives nine numbered steps of its
own, deliberately giving the pre-release checks no number: a number here
would claim they belong to this sequence and would drift from the one that
owns them.

The consequence is that an operator working the numbered list completes
every step, reaches the end, and has not run them. Completing a numbered
sequence reads as finished, and a check with no number leaves no blank.

Four minor releases demonstrate it. The periodic-review-scope check landed
2026-09-01; `v2.73.0`, `v2.74.0`, `v2.75.0` and `v2.76.0` were all tagged
2026-09-03 against a newest audit record of 2026-09-01, so each would have
failed the check identically. Each shipped owing a periodic review, under a
gate that existed, was correct, and was named in the PLAYBOOK the whole
time. The check was not broken and the procedure was not ignored — the
procedure had no place to notice the omission.

One mechanism for exactly this already existed and was scoped too narrowly.
The pre-release sequence's step 6 is both unenforced and unrecoverable, and
the rule covering it required the release proposal to name each step run by
hand and its result. That is the record this gap needs, applied to one step
out of eight.

## Decision

1. **The record covers the sequence, not one step** — the release proposal
   MUST name every step of the pre-release sequence and the result it
   produced, including each check the consuming runbook does not number.
   A step nobody ran is then a line the proposal does not carry, which is
   the only place its absence appears.

2. **The proposal is an artifact the procedure already produces** — for
   this repository it is the body of the changelog-cut pull request, which
   the no-build release variant already requires as its own pull request
   and which is reviewed before the tag exists.

3. **No pre-release check gains a step number in a consuming runbook** —
   the remedy MUST NOT introduce a number that means one thing in the
   runbook and another in the file that owns the sequence.

4. **The four cuts stand as history, discharged by the current record** —
   a periodic review is a statement about the tree at a date, not a
   per-release artifact. The `2026-09-03` record covers the tree those four
   releases shipped, so it discharges the obligation for all of them. They
   are not retagged, re-released, or annotated.

## Alternatives considered

- **Give the pre-release checks numbers of their own** — a lettered or
  separately-numbered pre-sequence, so an operator has something to leave
  blank. Rejected: it reintroduces cross-document step numbers for one
  check, which is the drift the sequence's naming rule exists to prevent.
- **Leave the checks unnumbered and unrecorded, and rely on the operator
  reading the prose above the list** — rejected; that is the arrangement
  under which the four cuts shipped.
- **Record one periodic review per release** — rejected; it makes the
  review a release artifact rather than a statement about the tree, and
  four records dated one day apart would say the same thing four times.
- **Retroactively annotate the four releases as having shipped owing the
  review** — rejected; the tags hold trees the current record covers, so
  the annotation would report a debt that no longer exists.

## Consequences

- `base/core/git.md`'s step-6 paragraph is split: step 6 keeps its own
  reason for being gated first, and the record requirement becomes a rule
  over the whole sequence.
- `docs/PLAYBOOK.md` step 4 names the changelog-cut pull request body as
  this repository's release proposal, and the paragraph explaining why the
  pre-release checks carry no number now says what makes them unskippable
  instead.
- A consuming project that renumbers or omits these steps in its own
  runbook inherits the record requirement rather than a numbering scheme,
  so the rule holds without constraining how the runbook is written.
- The requirement is enforced by review of the release pull request, not by
  a check. Nothing extracts the proposal and compares it against the
  sequence, so a proposal that names a step it did not run is not detected.
- `v2.73.0` through `v2.76.0` keep their tags, releases and milestones
  unchanged.
