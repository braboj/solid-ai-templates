---
id: SAIT-SMK-SYS-15-001A
title: A stack outside the exempt layers resolves the security tier
product: sait
type: smoke
area: SYS
priority: p1
status: ready
environment: [local, ci]
automatable: yes
created: 2026-09-06
author: Branimir Georgiev
product-version: "2.x"
tags: [composition, security, manifest, layer]
---

## Short description

> **Given** a manifest that classifies every stack by `layer`
> **When** each stack outside the exempt layers is resolved
> **Then** a chain carrying no `base-security` fails, because a stack
> that serves traffic and resolves no security rules produces a context
> file silent on input handling, auth and headers, and nothing in the
> generated output declares the tier absent

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every stack outside `library` and `embedded` resolves `base-security` |
| FAILED | A governed stack's chain carries no `base-security` |
| FAILED | A stack declares no `layer`, so the check cannot classify it |
| FAILED | The check reached no stacks, or named no exempt layers |
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

1. Load the manifest and take every entry whose file sits under
   `templates/stack/`
2. Read each stack's `layer`. A stack without one is a failure rather
   than a default, because the exemption is the thing being decided
3. Partition by layer against the exempt set, which names its reason
   per layer in the check rather than listing stack IDs
4. Resolve each governed stack's chain and test it for `base-security`
5. Report the stacks classified, the exempt layers named, and the
   stacks the check went on to require the tier of

### Assertions

1. Assert every governed stack's resolved chain carries `base-security`
2. Assert every stack carries a `layer`, since the classification the
   exemption rests on is read from it
3. Assert the stack count and the exempt-layer count are non-zero, per
   ADR-034: a check that classified nothing reports what a clean tree
   reports

### Negative controls

Each control was observed failing, and each mutation was asserted to
have landed in the parsed manifest before its result was read.

1. **A governed stack loses the tier.** Removing `base-security` from
   `backend-auth`'s `depends_on` MUST fail. Observed 2026-09-06:
   `backend-auth` went from `[backend-http, base-security]` to
   `[backend-http]` and the check named `stack-grpc-go` and
   `stack-grpc-python`, the two stacks that reach the tier through it
2. **A stack declares no layer.** Deleting `stack-flask`'s `layer` line
   MUST fail. Observed 2026-09-06: the layer went `backend` → absent,
   the check named the stack as unclassifiable, and the governed count
   moved 13 → 12, so the corpus is confirmed to have changed rather
   than the message alone
3. A first attempt at control 1 asserted only that some entry now
   depended on `backend-http` alone. `backend-api` already did, so the
   assertion would have passed had the edit not landed. The landing
   assertion names the mutated entry and compares its value before and
   after

## Related

- `SAIT-SMK-MNF-03-001A` — that every chain carries the core tier; this
  check is about a tier that is required of most stacks rather than all
- `SAIT-SMK-SYS-06-001A` — that a chain carries the MUST sections; that
  parity is within a stack's own file, this one is across its chain
- ADR-034 — why the counts are reported and floored

<!-- measured: 2026-09-06 -->

- Measured basis, 2026-09-06: 17 stacks, 2 exempt layers, 13 stacks
  required to resolve the tier. The exempt set is exactly `library` (3
  stacks) and `embedded` (1). Before the tier was restored to
  `stack-htmx`, that stack resolved nine files and no security template
  while every other check passed

<!-- /measured -->
