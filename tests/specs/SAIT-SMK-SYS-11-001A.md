---
id: SAIT-SMK-SYS-11-001A
title: Prose ID references resolve in every chain carrying the file
product: sait
type: smoke
area: SYS
priority: p2
status: ready
environment: [local, ci]
automatable: yes
created: 2026-08-28
author: Branimir Georgiev
product-version: "2.x"
tags: [composition, reach, section-ids]
---

## Short description

> **Given** a template whose running prose names another file's section
> ID
> **When** every stack chain that carries the referencing file is
> resolved
> **Then** the file declaring that section is present in all of them —
> otherwise the reference sends a reader to a section their own context
> file does not contain

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every cross-file prose ID reference resolves in all chains carrying the referencing file |
| FAILED | A reference dangles in at least one chain, or names an ID no template declares |
| FAILED | The check resolved no chains, or matched no references at all |
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

1. Resolve every stack's chain from the manifest
2. Map each declared section ID to the files declaring it
3. For each template, find backticked IDs in its prose that it does not
   declare itself
4. For each such reference, compare the chains carrying the referencing
   file against those carrying the declaring file

### Assertions

1. Assert no reference is missing from a chain that carries its
   referencing file
2. Assert the chain count is non-zero — a check that resolved nothing
   reports the same empty result as one that found nothing
3. Assert the reference count is non-zero — a pattern that stopped
   matching is indistinguishable from a clean tree otherwise

### Negative controls

1. Plant a reference to a section declared in a file no general chain
   carries; the check MUST fail and name the chains it is absent from
2. Alter the reference pattern so it still compiles and matches nothing;
   the check MUST fail on the reference count rather than pass. This is
   the shape a careless later edit takes, and it is the control the
   assertion in step 3 exists for

## Related

- `SAIT-SMK-TPL-04-001A` — covers EXTEND/OVERRIDE directives, which are
  structural; a prose reference is checked by neither it nor TPL-06
- `SAIT-SMK-TPL-06-001A` — the same reachability question for directives
- Measured basis, 2026-08-28: 15 cross-file prose references across the
  tree, of which 3 dangled — one in all 17 chains, because the file
  declaring it resolves into no chain at all
