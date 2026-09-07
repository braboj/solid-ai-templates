---
id: "044"
status: Accepted
date: 2026-09-07
category: composition
supersedes: []
superseded_by: []
---

# ADR-044: Rule-family membership is declared by category, not produced by the graph

## Context

A rule family reaches a stack when some template in that stack's chain
declares a dependency on it. Nothing else states which stacks should
carry it, so the set of stacks that do is a side effect of a few
declarations rather than a decision anyone recorded.

Measured on the quality-gate tier, that produced an asymmetry no reader
would defend. The tier resolved into twelve of seventeen stacks. A Node
library sat outside a family both its library-layer siblings carry; two
Node services missed it because they build from the base tier rather than
through a parent that declares it. A family answering how a gate is
retrofitted, ratcheted and retired is precisely as relevant to one
ecosystem's lint migration as to another's.

The composition model can already express membership by class of stack —
the security tier is required of every stack outside two named categories,
and a check enforces it. That mechanism had simply never been asked to
carry a second family. Adding a stack silently placed it inside or outside
every family, and no check had an opinion in either direction.

Membership also has a cost that is not free to ignore. Every category has
a recorded context tier, and a category at the most constrained tier
cannot take a large file without moving what that category requires of a
model. Measured before this decision, adding the quality-gate tier to the
two categories at the most constrained tier would have pushed both past
the budget that tier leaves.

## Decision

1. **Membership is declared** — a rule family that some stacks carry and
   others do not MUST have its membership stated by stack category, with
   a reason per exempt category, and MUST NOT be left to whatever the
   dependency graph produces.

2. **The declaration is by category, not by identifier** — the exemption
   names the categories the manifest already classifies stacks into, so a
   stack added later is governed or exempt by the class it declares
   rather than by a list that goes stale.

3. **A check enforces it in both directions** — a stack in a governed
   category resolving no member of the family fails, and a stack that
   declares no category fails rather than passing by omission.

4. **An exemption's stated reason MUST be falsifiable** — where the
   reason is a property recorded elsewhere in the tree, the check asserts
   the reason still holds. An exemption whose justification has expired
   reads as a decision and behaves as an omission, which is worse than
   having no exemption at all.

5. **The context tier is a legitimate reason** — a category recorded at
   the most constrained tier MAY be exempt on that basis, because
   admitting the family would change which models can run the stack.
   That is a cost to a consumer, so it is recorded rather than absorbed.

## Alternatives considered

- **Require every family of every stack** — rejected; a category at the
  most constrained context tier would lose that tier, which changes what
  the category requires of a model without anyone deciding to.
- **Declare membership as a list of stack identifiers** — rejected; the
  list is correct on the day it is written and silently wrong at the next
  stack, which is the failure this decision exists to remove.
- **State the policy in prose and gate nothing** — rejected; the prior
  state already had prose about what the tiers are for, and a membership
  no check reads is indistinguishable from an accident.
- **Defer until the core tier is smaller** — rejected as the general
  answer; it leaves the consumers in the gap with neither the rule nor a
  recorded reason. It remains the right answer for a specific category
  whose budget genuinely cannot take a family today, which is what the
  exemption expresses.

## Consequences

- Three stacks — the two Node services and the Node library — resolve the
  quality-gate tier, and their chains grow accordingly. None crosses its
  category's recorded context tier.
- Two categories are exempt on a recorded and checkable basis rather than
  by accident, and the exemption expires by itself if either category
  moves off the most constrained tier.
- A new stack cannot silently land outside a declared family: it either
  declares a governed category and resolves the family, or declares an
  exempt one, or fails.
- Any further rule family that some stacks carry and others do not owes
  the same declaration. The mechanism is now used twice, so a third use
  is a repetition rather than a design.
