---
id: "023"
status: Accepted
date: 2026-08-02
category: process
supersedes: []
superseded_by: []
---

# ADR-023: Carry deferral and urgency on labels, not milestone lanes

## Context

The issue guidance prescribed two named milestones that hold work rather
than schedule it. A `Backlog` milestone caught issues with no target
release, so that "unmilestoned" and "deliberately unscheduled" stayed
distinguishable. An `Expedite` milestone was a rolling fast-track lane
for out-of-cycle work; by definition it never closed.

Both are milestones doing a label's job. A milestone answers "which
release is this in"; these two answered "is this parked" and "is this
urgent" — properties of the issue, not of a release. The mismatch has
costs that showed up in use:

- A lane that never closes accumulates indefinitely and stops being a
  planning signal. `Expedite` shipped nine issues across four months and
  spent most of that time empty or holding one item.
- The two lanes compete with the labels that already encode the same
  facts. Deferral is `P4`; urgency is the severity band. An issue could
  be `P4` and `Backlog`-milestoned, or `P0` and not in `Expedite`, with
  no rule for which reading won.
- A milestone's meaning is not durable. Closing or deleting one strips
  the field from every attached issue, and the "deliberately unscheduled"
  fact it carried is gone — where a label survives.

The priority scale had already moved. `P4` was redefined as a deferral
marker orthogonal to severity, which is exactly what the `Backlog` lane
was for. The deferred-work rule was not updated to match, and went on
calling its `Backlog` issue "distinct from a P4 'someday' issue" — a
description of a band that no longer exists.

## Decision

1. **No named holding lanes** — a project MUST NOT stand up a `Backlog`,
   `Expedite`, or equivalent milestone to mark work as unscheduled or
   fast-tracked. Milestones remain optional, forward-looking, and scoped
   to a planned release.

2. **Deferral is a label** — deliberately deferred work MUST carry the
   `P4` marker plus explicitly named trigger conditions on the issue.

3. **Urgency is severity** — out-of-cycle or fast-tracked work is
   identified by its severity band. It needs no separate lane to be
   findable.

4. **An unscheduled release needs no milestone** — a routine or emergent
   release that was never scoped as a milestone gets none; the Release is
   its shipped record.

## Alternatives considered

- **Keep both lanes, document the precedence against the labels** —
  rejected; it preserves two encodings of one fact and adds a rule to
  arbitrate them, which is more surface than either lane earns.
- **Keep `Backlog`, drop `Expedite`** — rejected; `Backlog` is the one
  fully subsumed by `P4`, so this keeps the redundant lane and drops the
  one with a distinct (if weak) meaning.
- **Close the lanes rather than forbidding them** — rejected as the rule;
  closing is a fine local migration step, but the guidance has to say
  what to do instead, or the next project rebuilds them.
- **Replace the lanes with a `deferred` label** — rejected; `P4` already
  is that label, and adding a synonym repeats the original error.

## Consequences

- `platform/github.md` drops the `Backlog` routing rule and the
  `Expedite` lane paragraph, and no longer names either milestone in the
  release-record rule.
- `base/workflow/issues.md` restates the deferred-work rule against `P4`,
  resolving its contradiction with the priority scale.
- Projects running these lanes migrate by labelling the open issues
  `P4` (for `Backlog`) or by severity alone (for `Expedite`), then
  deleting the milestones. Attached closed issues lose the milestone
  field; the Release record is the shipped history.
- Nothing distinguishes "untriaged" from "deliberately unscheduled"
  except the `P4` label, so applying it at deferral time is now
  load-bearing rather than advisory.
