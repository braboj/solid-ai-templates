---
id: "039"
status: Accepted
date: 2026-09-06
category: composition
supersedes: []
superseded_by: []
---

# ADR-039: A chain overrides each section ID once, and specialises through a new ID

## Context

The composition model lets a template replace an inherited section with
`[OVERRIDE: <id>]`. Nothing constrained how many templates in one resolved
chain may claim the same ID.

`docs/SPEC.md` called a double override an error and stated no winner: the
agent was told to surface the conflict and ask. The tree did it anyway. The
`stack-tutorial` chain carried two replacements each of
`static-site-architecture`, `static-site-content` and `static-site-assets` —
one from `static-site-astro.md`, one from `static-site-tutorial.md`, which
depends on it. The resolved file carried both bodies, saying in one place
that content lives in `src/data/` as JSON and in another that it lives in
`chapters/` as Markdown.

No check reported it. The directive checks verify that an `EXTEND` or
`OVERRIDE` target exists and is reachable in the chain; none counted how
many templates claimed one. So the rule the specification named as an error
was a rule nothing enforced, and a stack shipped for months with the
conflict resolved by whichever body the agent read last.

A three-level chain elsewhere in the tree had already solved this without
anyone stating the pattern: `go-lib` to `go-service` to `go-echo`, where
each level's overriding section declares an ID of its own and the next
level overrides that.

## Decision

1. **One override per ID per chain** — no resolved chain MUST contain more
   than one template overriding a given section ID. This holds for stack
   chains and for the chains of orthogonal roots alike.

2. **Specialisation goes through a new ID** — a section that overrides and
   expects further specialisation MUST declare an `[ID:]` of its own. A
   downstream template overrides that ID, not the one its dependency
   already claimed. Each level stays addressable, and the reader meets one
   authority per ID at each depth.

3. **The constraint is checked, not advised** — a smoke check collects the
   override targets per resolved chain and fails an ID claimed twice. A
   composition rule stated only in prose is one the tree can violate
   silently, which is how this one survived.

## Alternatives considered

| Alternative | Rejected because |
| --- | --- |
| Amend the specification so the later template in the chain wins | It legitimises a chain that ships two contradictory bodies for one section. The agent reads both, and nothing in the resolved file says which is dead. Chain order already decides file order; making it decide meaning as well hides the conflict rather than removing it |
| Leave the rule as prose and rely on review | The rule was already prose, and three collisions in one chain passed review, five tools and every gate |
| Give the downstream template private IDs and drop the override | The upstream body then stays in the chain unreplaced, which is the same two-authorities problem with an extra section |

## Consequences

- `templates/stack/static-site-astro.md` declares `astro-architecture`,
  `astro-content` and `astro-assets`; `templates/stack/static-site-tutorial.md`
  overrides those under IDs of its own.
- `docs/SPEC.md` states the specialisation pattern beside the conflict table
  that names the error.
- A stack depending on another stack pays three ID declarations' worth of
  chain characters to specialise a section. The chain budget prices it.
- The check reads orthogonal roots as well as stacks, so a collision inside
  an opt-in chain is a finding rather than a blind spot.
