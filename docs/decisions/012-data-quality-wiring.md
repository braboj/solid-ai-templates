---
id: "012"
status: Accepted
date: 2026-06-03
category: composition
supersedes: []
superseded_by: []
---

# ADR-012: Wire base-data-quality into stack-python-service only

## Context

`templates/base/data/data-quality.md` was added in v2.8 with four
sections — calibration discipline, cross-validation and tool trust,
data-research workflow, gate scope agreement. The file is registered
in `manifest.yaml` as `base-data-quality` (depends_on:
`base-data-modeling`).

No stack declared `base-data-quality` in its `[DEPENDS ON: ...]`
chain. The rules were discoverable when browsing `templates/base/`
but never reached `generated/<stack-id>.md` — projects generating
context from a stack pre-resolved chain never saw them. The v2.8
milestone summary flagged this as a gap and deferred the fix to
v2.9 (#418).

Two architectural paths existed:

1. Wire the data layer into existing backend stacks now.
2. Defer to the planned `data-heavy` stack (#298) and keep
   `base-data-quality` opt-in via fork-and-extend.

Path 2 is the cleaner long-term shape but leaves the v2.8 content
unreachable until v3.0. Path 1 closes the gap immediately.

The four sections in `data-quality.md` are not strictly about
data — calibration, cross-validation, and research-workflow rules
apply to any project where an agent does investigative work. The
file naming overstates the data-heavy framing. Splitting the file
is future work, out of scope for #418.

## Decision

1. **Wire only via stack-python-service** — `base-data-quality`
   MUST appear in the `depends_on` list of `stack-python-service`
   and in the `[DEPENDS ON: ...]` header of
   `templates/stack/python-service.md`. It MUST NOT be added to
   other stacks in this change.
2. **Propagation is transitive** — Flask, FastAPI, and Django
   inherit `base-data-quality` automatically via their dependence
   on `stack-python-service`. No direct edits to those stacks.
3. **Other backend stacks remain unwired** — Go, Node, Java, and
   Celery stacks do NOT gain `base-data-quality` in this ADR.
   Wiring them is a separate decision, gated on either a file
   split or an explicit broader-rollout ADR.

## Alternatives considered

- **Wire into all backend stacks** — rejected; pulls
  data-modeling rules into stateless services and forces a
  broader rollout decision before the file-naming question is
  settled.
- **Defer to #298 data-heavy stack** — rejected; leaves v2.8
  content unreachable until v3.0 with no interim mitigation, and
  the four sections apply more broadly than a single data-heavy
  variant.
- **Split data-quality.md first** — rejected as scope creep for
  #418; the split is recorded as follow-up work.

## Consequences

- `generated/stack-python-service.md`, `generated/stack-flask.md`,
  `generated/stack-fastapi.md`, and `generated/stack-django.md`
  include data-quality content after `py tools/sync.py`.
- The v2.8 memory note about the gap is resolved for Python
  service stacks.
- A follow-up issue tracks the file-naming and split question
  (calibration/research rules vs. true data-heavy rules).
- Go, Node, Java, and Celery stacks remain in the gap until the
  follow-up decision lands.

## Related

- #418 — wiring task this ADR records
- #298 — `data-heavy` stack proposal, still in v3.0 milestone
- ADR-009 — stack scope cap, fork-and-extend model
