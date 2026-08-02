---
id: "024"
status: Accepted
date: 2026-08-02
category: process
supersedes: ["021"]
superseded_by: []
---

# ADR-024: Priority is severity only, and the milestone field carries deferral

## Context

The priority scale carries four severities plus a fifth label that is
not a severity but a scheduling statement. Alongside it, a named
holding milestone once carried the same scheduling signal. That lane
has since been deleted, on the reasoning that a lane's meaning is lost
when the milestone is closed while a label travels with the issue —
which left the marker as the sole carrier of deferral.

Sole carrier is the right shape; this marker is the wrong carrier. It
overlaps the milestone field rather than complementing it. An issue can
be marked deferred while sitting in a planned cut, or unmarked while
sitting in no milestone at all, and both combinations exist in the
tracker this was measured on: of four open issues carrying the marker,
two also carry a milestone and two carry none. In neither pair does the
marker say anything the milestone field does not already say.

The earlier reasoning kept the marker because dropping it would push
deferral into prose, where it stops being filterable. That assumed the
alternative to a label was prose. It is not. The milestone field is
itself a first-class, filterable axis, already mandatory reading when
scoping a release, and already documented as optional — an empty
milestone is a valid state meaning the work is not tied to a release.
Deferral was being recorded twice, in a label and in a field that
encodes the same fact.

## Decision

1. **Priority is severity only** — the scale is `P0` critical, `P1`
   high, `P2` medium, `P3` low. Every issue MUST carry exactly one
   band. There MUST NOT be a fifth priority label.

2. **The milestone field carries deferral** — a milestoned issue is
   planned into that cut; an unmilestoned issue is backlog. Deferral
   MUST NOT be recorded as a label, and MUST NOT be recorded as a
   named holding milestone.

3. **Triage is labels, not milestones** — an issue is triaged when it
   carries a type and a severity, which the at-creation rule already
   requires. An empty milestone field therefore MUST NOT be read as
   untriaged; it means unscheduled.

4. **Deferred work still names its triggers** — an unmilestoned issue
   that is deliberately deferred MUST state its trigger conditions in
   the body. The milestone field records that the work is unscheduled;
   the body records what would schedule it.

## Alternatives considered

- **Keep the marker as an orthogonal label** — rejected; it duplicates
  the milestone field, and two carriers for one signal can disagree
  without either being wrong.
- **Rename the marker to `deferred`** — rejected; the name was never
  the problem. A non-priority name leaves the same duplication.
- **Re-introduce a named holding milestone** — rejected; a lane's
  meaning is lost the moment the milestone is closed or deleted, and
  it competes with dated cuts for the same field.
- **Close deferred work with a triage label** — rejected; the triage
  labels are terminal and record a decision not to act. Deferred work
  is work the project still intends to do.

## Consequences

- `base/workflow/issues.md` drops the marker from the priority table
  and restates its deferred-work section against the milestone field.
- `platform/github.md` drops its deferral label table, and its label
  conformance check no longer needs a caveat explaining why a fifth
  band is excluded from the priority pattern.
- `platform/linear.md` restates its label and priority sections over
  `P0`–`P3`; the prohibition on recreating priority as labels narrows
  to the four bands that exist.
- `CLAUDE.md` §2.2 drops the deferral label table.
- The `P4` label is deleted from the repository, which strips it from
  closed issues as well as open ones. Issues that carried it keep their
  severity and their milestone, or their absence of one, which already
  states their scheduling.
- Deferred work becomes discoverable by an empty-milestone filter
  rather than a label filter. Trigger conditions in the issue body
  remain the record that a deferral was deliberate rather than an
  oversight.
- A deferred-work rule previously stated against the marker is restated
  against the milestone field. The prohibition on named holding
  milestones is unaffected.
