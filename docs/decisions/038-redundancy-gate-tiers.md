---
id: "038"
status: Accepted
date: 2026-09-05
category: tooling
supersedes: []
superseded_by: []
---

# ADR-038: The redundancy gate fails on exact duplicates and reports near ones

## Context

`tools/audit_redundancy.py` finds a rule stated twice inside one resolved
chain, which is a cost a consumer pays on every turn. It reports two tiers:
exact duplicates, and near duplicates scored by a similarity ratio and shown
only under `--near`. CI runs `--check`, which fails on exact duplicates
outside a baseline that is currently empty.

The audit resolved 17 of the 37 roots a project can pick, because it looped
over stacks and ADR-035 has every orthogonal template resolving as its own
root. Widened to all 37, the near tier goes from 3 findings to 6. The widest
of the newly visible pairs scores 0.99: `base/core/git.md` and
`base/workflow/release.md` both carry a `Versioning` section, and both
resolve into the `base-release` chain, so a project picking that extra
receives the rule twice.

That pair was invisible from two directions at once -- outside the scanned
roots, and below the gated tier. Widening the roots fixes the first. This
decision settles the second.

## Decision

`--check` continues to fail on exact in-chain duplicates only. The near tier
stays advisory.

`--check` additionally prints the near-duplicate count on every run,
including a passing one, so a green gate states what it did not gate.

## Alternatives considered

**Gate the near tier above a similarity threshold.** Rejected. The ratio is
a judgement rendered as a number: 0.90 separates "the same rule twice" from
"two rules that share vocabulary" only sometimes, and the four findings
between 0.90 and 0.96 in the current tree include pairs that are legitimate
restatements addressed at different audiences. A gate on that number fails on
correct content, and the repair for a false positive is a baseline entry --
which is how a baseline that is meant to shrink starts growing instead. The
project already has one number that has been raised 313 times and lowered
none.

**Leave `--check` silent about the near tier.** Rejected. It is what let the
0.99 pair survive: the gate passed, printed nothing about what it had not
looked at, and a reader took `OK` to mean no duplicates rather than no exact
duplicates. A check that reports only its verdict reads the same whether its
unscored tier is empty or full.

**Score near duplicates as exact by lowering the exact threshold.** Rejected.
Exact means byte-identical after normalisation, which is a predicate. Making
it fuzzy would delete the one tier that needs no judgement.

## Consequences

A near-duplicate pair cannot fail CI, so removing one stays a deliberate act
rather than a forced one. The count in the gate output is what makes it
visible; a project watching that number rise has the signal the previous
arrangement withheld.

The 0.99 `Versioning` pair is a real duplicate in a shipping chain and is now
reported on every `--check` run. Resolving it is content work on two
templates and is not part of this decision.

The audit's cost rises with the wider root set, since it resolves 37 chains
rather than 17.
