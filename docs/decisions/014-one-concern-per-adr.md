---
id: "014"
status: Accepted
date: 2026-06-24
category: process
supersedes: []
superseded_by: []
---

# ADR-014: One concern per ADR

## Context

The "one concern, one PR" rule is explicit for pull requests but only
implicit for ADRs. The single `category` field, the singular framing in
the ADR template, atomic supersession, and the self-sufficiency
requirement all imply it, yet no written rule states it. When an ADR
grows to cover two concerns — for example a content-layout decision and
a build-output decision — there is nothing to cite when splitting the
second concern into its own record.

## Decision

1. **One concern per ADR** — each ADR MUST address exactly one concern.
   A separate concern gets its own ADR, cross-linked or superseding via
   the frontmatter `supersedes` / `superseded_by` fields as needed.
2. **One concern is not one rule** — a single ADR MAY number multiple
   related decisions (1., 2., …) within its one concern. The constraint
   is on the topic, not the count of rule statements.

## Alternatives considered

- **Leave it implicit** — rejected; unenforceable in review with no
  written rule to cite when a multi-concern ADR appears.
- **One rule per ADR** — rejected; over-fragments governance ADRs that
  legitimately bundle related sub-decisions under a single concern.

## Consequences

- `base/core/docs.md`, `CLAUDE.md` §2.9, and `docs/decisions/TEMPLATE.md`
  state the rule; the template note clarifies that one concern is not
  one rule.
- No schema change; the smoke `ADR-01` check is unaffected.

## Related

- #489 — the task this ADR records
