---
id: SAIT-SMK-SYS-18-001A
title: A stack outside the constrained categories resolves the gate tier
product: sait
type: smoke
area: SYS
priority: p1
status: ready
environment: [local, ci]
automatable: yes
created: 2026-09-07
author: Branimir Georgiev
product-version: "2.x"
tags: [composition, membership, quality-gates, context-window]
---

## Short description

> **Given** a declared membership policy for the quality-gate tier, stated
> by stack category rather than by a list of stack identifiers
> **When** every stack's category is read from the manifest and its
> resolved chain inspected for the tier
> **Then** a stack in a governed category that resolves no gate tier
> fails, because membership was otherwise whatever the dependency
> declarations happened to produce and no check had an opinion in either
> direction

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every stack in a governed category resolves the gate tier, and each exempt category is still recorded at the most constrained context tier |
| FAILED | A stack in a governed category resolves no gate tier |
| FAILED | A stack declares no `layer`, so the check cannot classify it |
| FAILED | An exempt category has no recorded context tier |
| FAILED | An exempt category is recorded above the most constrained tier, so the stated reason has expired |
| FAILED | The check read no categories, no exemptions or no stacks |
| SKIPPED | PyYAML not installed |
| BLOCKED | — |
| ERROR | — |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3 with PyYAML

### Setup

— (operates on the committed tree)

### Execution

1. Read the recorded context tier per category and find the most
   constrained one
2. Confirm each exempt category is recorded at that tier
3. Classify every stack by its manifest `layer`
4. Resolve each governed stack's chain and look for the gate tier
5. Report the categories recorded, the exemptions named, the stacks
   classified and the stacks governed

### Assertions

1. Assert every governed stack resolves the gate tier
2. Assert an unclassified stack fails rather than passing by omission —
   a stack with no `layer` is the case this check exists to notice
3. Assert each exemption's stated reason still holds against the tier
   record, so an exemption cannot outlive the constraint that justified
   it and keep reading as a decision
4. Assert the counts are non-zero, per ADR-034

### Negative controls

Each control was observed failing, and each mutation was asserted to
have landed before its result was read.

1. **The defect that motivated the check.** Run before the dependency
   declarations were added, the check named `stack-express`,
   `stack-nestjs` and `stack-nodejs-lib`, each in a governed category and
   resolving no gate tier. Observed 2026-09-07
2. **A dropped declaration.** Removing the tier from
   `stack-python-lib`'s `depends_on` MUST fail, with the governed count
   unchanged and the stack named
3. **An expired exemption.** Recording an exempt category above the most
   constrained tier MUST fail on the reason rather than on membership,
   which is what separates the two halves of the check

## Related

- `SAIT-SMK-SYS-15-001A` — the same shape for the security tier, and the
  precedent that a tier's membership is declared by category rather than
  by a list of stack identifiers that goes stale
- `SAIT-SMK-SYS-16-001A` — the tier record this check reads its
  exemptions against
