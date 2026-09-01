---
id: "033"
status: Accepted
date: 2026-09-01
category: process
supersedes: []
superseded_by: []
---

# ADR-033: A periodic review is owed by minor and major releases only

## Context

The pre-release sequence in `base-git` names a periodic project-wide audit
as its third step, and the quality-gates rules encourage pairing a stated
constraint with a check. A project that does both arrives at a review
attached to the release event: run the audit, or record why you declined
it, before every tag.

Most releases are patches. A patch fixes a defect and changes no
interface, so a review whose subject is the shape of the project has
nothing new to read on one. The operator writes a document saying so and
the tag proceeds.

Two consecutive releases in a consuming project declined the audit,
neither having changed a source module — one carrying documentation and a
test policy change, the other a gate comparison, a record and
documentation. Three releases then rested on a single report, and the
decline was becoming the routine way to clear the gate rather than the
exception it was written as.

The existing rules do not catch this. The rule covering a constraint with
no check does not apply, because the check exists. The rule covering a
step nothing enforces does not apply, because the step is enforced. The
gate is neither too weak nor too strong; it is scoped to the wrong event,
and every signal available says it is working.

It also resists the obvious repair. Replacing the obligation with a
condition — the next audit when the open backlog reaches zero — schedules
nothing, because nothing polls a backlog and no release meets the
condition.

Before this decision, `base-git`'s own enforcement table rated the step as
carrying no pass condition in either direction, so the step was both
unenforced and attached to an event class that mostly could not produce a
finding.

## Decision

1. **Scope by release kind** — a minor or major release MUST carry a
   current periodic review where the project runs one. A patch release
   owes nothing: neither the report nor a record declining it.

2. **An unreadable version is a finding** — a version the gate cannot
   parse MUST fail rather than skip. An unreadable version and an exempt
   version both mean the comparison does not run, and reading them alike
   turns a typo in a version literal into a silent exemption.

3. **The narrowing re-points its own controls** — a change narrowing what
   a gate evaluates MUST confirm the gate's negative controls still fire.
   Fixtures named with a patch version stop firing the moment the gate
   skips patches, leaving the suite green while testing nothing.

4. **The step ships a check** — the obligation is mechanically decidable
   from the version and the dated records, so `base-git` carries a
   runnable check with a stated pass condition rather than prose alone.

## Alternatives considered

- **Leave the obligation on every release** — rejected; the failure is
  not hypothetical, and its cost is an erosion of the rule rather than a
  false positive. The cheapest compliant path stops involving the work.
- **Warning only, no gate change** — rejected; it is the narrower claim
  the observation would defend, but it leaves the step unenforced in both
  directions and asks the operator to notice a decay that by construction
  looks like compliance.
- **Calendar-based cadence** — rejected; it decouples the review from the
  changes it reads, so a quiet quarter owes a review and a busy one may
  not.
- **Diff-based scoping** — rejected; deciding whether a diff can move a
  project-wide review is the judgement the review itself makes, so the
  gate would need the review's answer to decide whether to ask for it.
- **Defer against a backlog condition** — rejected; nothing polls a
  backlog, so a deferral with no watcher reads exactly like a live
  obligation.

## Consequences

- `templates/base/core/git.md` gains the periodic-review-scope check and
  the rule beside it; pre-release step 3 and its enforcement table row
  change accordingly.
- `tests/conformance.py` gains the check's disposition. It reports as not
  applicable in this repository, which sets no release version.
- A consuming project whose releases are mostly patches stops producing
  decline records, which were the artifact the gate had begun to collect
  in place of reviews.
- This repository becomes measurably in arrears: its newest audit record
  predates its last release, and its next release moves the minor
  version, so the check reports a finding it must answer before cutting.

## Related

The scoping question is a release-process concern; the currency
comparison the check performs is stated in `base-git` beside it.
