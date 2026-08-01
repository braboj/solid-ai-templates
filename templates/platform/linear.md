# Platform — Linear

[ID: platform-linear]
[DEPENDS ON: templates/base/workflow/issues.md]

Linear-specific issue tracking. Implements the base issue taxonomy in
Linear-native primitives — label groups, the priority field, workflow
states, sub-issues — rather than re-encoding it as flat labels.

---

## Composition

[ID: platform-linear-composition]

- Linear carries the tracker ONLY. Pair it with a code-host platform
  template (`platform/github.md`) that carries CI, SAST, secret
  detection, and dependency management.
- A project MAY declare two platform templates when one of them is
  Linear. Two code-host platforms remain mutually exclusive.
- Where a rule appears in both, the code-host template governs the
  repository and this template governs the tracker.

---

## Issue labels

[ID: platform-linear-labels]
[EXTEND: base-issues-types]

Linear label groups are mutually exclusive. Put the type taxonomy in a
group so "exactly one type" is enforced by the tool rather than by
convention.

- Create a label group named `Type`. Every type label MUST sit inside
  it.
- Type label names MUST match the code-host platform template character
  for character, lowercase included — a label differing only by case
  does not round-trip through the code-host integration.
- MUST NOT create `P0`–`P4` labels. Priority is a native field; see
  `platform-linear-priority`.
- MUST NOT create `duplicate` or `wontdo` labels. Both are native
  workflow states; see `platform-linear-triage`.
- Cross-cutting labels (`security`, `tech-debt`, `docs`) MUST stay
  outside every group. An issue can carry more than one, and a group
  forbids that.

### Type labels (pick one)

| Label      | Color     | Maps to  |
| ---------- | --------- | -------- |
| `bug`      | `#C9372C` | Bug      |
| `epic`     | `#9F8FEF` | Epic     |
| `task`     | `#579DFF` | Task     |
| `spike`    | `#6CC3E0` | Spike    |
| `incident` | `#AE2E24` | Incident |

**Check:** list the team's issue labels. Every row above MUST report a
parent of `Type` and a non-null team, no row MUST appear a second time
outside the group, and no label named `P0`–`P4`, `duplicate`, or
`wontdo` MUST exist.

---

## Label scope

[ID: platform-linear-label-scope]

A Linear label belongs either to the workspace or to one team, and the
two do not mix. Migrating an existing workspace onto the taxonomy above
fails on this unless the order is right.

- A label group is team-scoped. A workspace label MUST NOT be parented
  into one — Linear rejects it as a team mismatch.
- Linear's stock `Bug`, `Feature` and `Improvement` labels are
  workspace-scoped, so the labels a workspace already has are exactly
  the ones that cannot join the group. Recreate the ones worth keeping
  as team labels.
- Label names are reserved workspace-wide. To replace a workspace label
  with a team label of the same name: rename the original to free the
  name, create the replacement inside the group, apply it to every issue
  that carried the original, and only then delete the original.
  Deleting first strips the label from every issue in the gap.
- Retiring one grouped label into another MUST rewrite the issue's whole
  label set in one update. A group admits one label, so adding the
  replacement first is rejected, and removing first leaves the issue
  untyped while the write is in flight.
- After deleting a label, re-read the label list and delete any residual
  copy. `issueLabelDelete` reports success while leaving an ungrouped
  duplicate carrying the label's pre-rename colour, so a migration that
  trusts the return value leaves the workspace dirty.

---

## Priority

[ID: platform-linear-priority]

Linear's native priority field carries four named severities plus an
unset value. Use it — a label cannot drive board ordering or saved
filters.

| Base | Linear field | API value |
| ---- | ------------ | --------- |
| P0   | Urgent       | 1         |
| P1   | High         | 2         |
| P2   | Medium       | 3         |
| P3   | Low          | 4         |

- Set a severity at creation.
- `No priority` (0) MUST mean untriaged, and MUST NOT be used for any
  severity. It is the default for an untouched issue, so spending it on
  a severity makes deliberate decisions indistinguishable from absent
  ones.
- `P4` is a deferral marker, not a severity, so it has no place in this
  field. Carry it as a label outside every group, or as the tracker's
  own deferral mechanism.

---

## Workflow states

[ID: platform-linear-states]

A Linear state carries a `type` that drives automation; its display
name is free text. Map the types, not the names.

| Type        | Purpose                           |
| ----------- | --------------------------------- |
| `backlog`   | Accepted, not scheduled           |
| `unstarted` | Scheduled, not begun              |
| `started`   | In flight — MAY be several states |
| `completed` | Shipped                           |
| `canceled`  | Will not be done                  |

- A team MUST expose at least one state of each type above.
- Split `started` into a working state and a review state when PR
  review is a distinct wait. The code-host integration targets a
  `started` state on PR open and a `completed` state on merge, so the
  split costs nothing to automate.

---

## Triage

[ID: platform-linear-triage]

Record terminal outcomes as states, not labels.

| Outcome                   | Linear mechanism               |
| ------------------------- | ------------------------------ |
| Already tracked elsewhere | Mark duplicate of the original |
| Acknowledged, will not do | `canceled` state               |

- Marking an issue duplicate MUST link the original. That link is an
  audit trail a `duplicate` label cannot carry.
- Enable the Triage inbox when issues arrive from outside the team —
  integrations, support, code-host issue sync. Triage is a holding
  area, not a state: an issue MUST leave it with a type label and a
  priority.

---

## Hierarchy

[ID: platform-linear-hierarchy]

Linear tracks parent and child natively and rolls up progress.

- An epic MUST use sub-issues for its children, and MUST NOT maintain a
  Markdown checklist of issue references. Linear computes the progress
  bar from sub-issue state; a hand-maintained checklist goes stale by
  construction.
- The `epic` type label still applies to the parent, so a type filter
  behaves identically on both platforms.
- Nest one level. A sub-issue needing children of its own is an epic.

---

## Projects and cycles

[ID: platform-linear-planning]

- A project groups issues by deliverable and MAY carry milestones.
  Neither is required — an issue with no project is valid.
- Cycles are time-boxed iterations, and are off by default. Enable them
  only when the team commits to a fixed cadence; an unused cycle is
  noise on every board.
- MUST NOT create a project solely to hold otherwise-unfiled issues. A
  catch-all project carries no planning information.

---

## Code-host integration

[ID: platform-linear-codehost]

- Install the code-host integration from Linear's settings and grant it
  every repository the team tracks, so a new repository needs no second
  setup step.
- A branch name MUST contain the issue identifier for the integration
  to link it. Combine with the code-host branch convention:
  `feat/<identifier>-<scope>`.
- Configure the automation to move an issue to a `started` state on PR
  open and to a `completed` state on merge.
- Two-way issue sync duplicates the tracker. Enable it per repository
  only where the code host is the source of truth for that repository;
  leave it off otherwise.
