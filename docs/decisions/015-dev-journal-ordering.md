---
id: "015"
status: Accepted
date: 2026-06-26
category: process
supersedes: []
superseded_by: []
---

# ADR-015: Dev-journal entries are ordered oldest-first

## Context

The dev-journal ordering rule was flipped from chronological (oldest
first, newest last) to reverse-chronological (newest first) in the change
that reconciled `base/core/docs.md` to this repo's own journal, which had
organically drifted to newest-first. That flip carried no recorded
rationale — it rode inside a PR whose stated subject was the journal
filename casing and required-contents schema, not ordering. No ADR
captured why newest-first is preferable.

The cost surfaced downstream: a long-running consumer journal (188
entries) that kept the original oldest-first order was flagged as
deviating from a mandated format that itself had no justification. The
"deviation" was in fact the original convention; the template had moved
away from it by accident. The ordering is settled here deliberately so it
stops being an unexplained default.

## Decision

1. **Oldest-first** — dev-journal session entries MUST be in chronological
   order: oldest first, newest at the bottom, directly under the
   architecture-overview block. The `## YYYY-MM-DD — theme` heading format
   and bold-labelled fields are unchanged; only the ordering is restored.

## Alternatives considered

- **Keep newest-first** — rejected; no recorded rationale, and it forces
  every long-running downstream journal to either rewrite its full history
  or carry a standing deviation. The marginal "most recent entry visible
  first" benefit does not justify that cost.
- **Make ordering project-configurable** — rejected; a single default
  keeps generated context files uniform and avoids per-project drift. A
  forked convention is harder to validate than one settled order.

## Consequences

- `base/core/docs.md` states oldest-first; the 30 generated chains were
  regenerated to match.
- This repo's `docs/dev-journal.md` was reordered to oldest-first (36
  entries) so the repo matches its own rule.
- The ordering half of #618's flagged deviation dissolves; its remaining
  heading/byline question stays open under the v3.0 restructure.

## Related

- #618 — the downstream deviation that surfaced the missing rationale.
- #500 / PR #543 — the change that introduced the unexplained flip.
