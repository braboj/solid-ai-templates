---
id: "043"
status: Accepted
date: 2026-09-07
category: composition
supersedes: []
superseded_by: []
---

# ADR-043: Declaring a core-tier file is redundant, not forbidden

## Context

The resolver seeds the core tier into every chain, so a stack does not
have to name those files. The specification went further and said no
`[DEPENDS ON:]` directive anywhere in the tree declares one, which made
the seeding the only route by which they are reached.

The tree has never matched that. Measured on the release commit, 43
directive tokens across 19 templates name a core-tier file, and 19
manifest entries name a core id in `depends_on`. Only one core file is
reached by the seeding alone; the rest are declared somewhere as well.

Nothing decided whether those declarations were wanted. The
specification denied they existed, so the question of what they mean was
never put. And a reader consulting it to understand why a file appears in
a chain they did not ask for was reading a sentence the tree contradicts.
Two answers were available and incompatible: sweep them out and gate
against their return, or keep them and say what they are.

The choice is not cosmetic. It decides whether a template author writing
a new file may name the core dependency it actually has, and it decides
whether a walk of the directives alone is a meaningful view of the graph.

## Decision

1. **Redundant** — a template MAY declare a core-tier file in
   `[DEPENDS ON:]` or in a manifest `depends_on`. The resolver reaches the
   file through the seeding either way, and the duplicate is deduplicated
   rather than rejected.

2. **Not load-bearing** — a chain MUST NOT depend on such a declaration
   for the file to resolve. The seeding is the guarantee; the directive
   documents a dependency a reader would otherwise infer, and removing it
   changes what the file says about itself and not what the chain
   contains.

3. **Stated by measurement** — the specification MUST state the core tier
   and the declaration counts from a generated block a staleness gate
   reads. A claim about the shape of the tree, written by hand, is right
   on the day it is typed.

## Alternatives considered

| Alternative | Rejected because |
| --- | --- |
| Forbid the declarations, sweep all 43, add a smoke check | The resolver has always deduplicated them; the sweep would reorder resolved chains and rewrite every generated file for no stated benefit, and it removes information a reader uses |
| Correct the sentence by hand and leave it ungated | The identical failure being repaired. The claim was false for an unknown length of time precisely because nothing read it |
| Say nothing about the declarations and only delete the false absolute | Leaves the question a reader arrives with unanswered, which is what made the original sentence load-bearing |

## Consequences

- `docs/SPEC.md` carries a generated `spec-core-tier` block: the file
  list, the measured declaration counts, and the core files reached by
  the seeding alone. `sync.py --check` fails when it drifts
- `README.md`'s prompt block no longer tells an agent that no directive
  declares the core tier
- `review` is a core-tier file and is removed from the opt-in tier table,
  where it also appeared
- A template author may name a core dependency without a check objecting,
  and a reviewer has a written answer for why the duplicate stands
- A walk of the directives alone remains an incomplete view of a chain,
  and the reconciliation between that walk and the resolver stays the
  check that says so
