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
| FAILED | A reference dangles in at least one chain, or an ID-shaped token no template declares is named |
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
3. For each template, find the backticked tokens in its prose that the
   declared-ID map holds and the file does not declare itself. The set of
   IDs decides what a reference is — a pattern built from layer prefixes
   sees file-level IDs and misses the section-level ones the rule is about
4. For each such reference, compare the chains carrying the referencing
   file against those carrying the declaring file
5. Report the number of declared IDs, the number named in another file's
   prose, the references checked and the chains resolved

### Assertions

1. Assert no reference is missing from a chain that carries its
   referencing file
2. Assert the chain count is non-zero — a check that resolved nothing
   reports the same empty result as one that found nothing
3. Assert the reference count is non-zero — a pattern that stopped
   matching is indistinguishable from a clean tree otherwise
4. Assert the run states how many IDs the check can see, so a pattern
   that narrows takes a visible number down with it

### Negative controls

1. Plant a reference to a section declared in a file no general chain
   carries; the check MUST fail and name the chains it is absent from
2. Alter the reference pattern so it still compiles and matches nothing;
   the check MUST fail on the reference count rather than pass. This is
   the shape a careless later edit takes, and it is the control the
   assertion in step 3 exists for
3. Narrow the pattern to a layer-prefix list; the reported reference
   count MUST drop. A widening that leaves the count unmoved changed
   nothing, whatever the pattern now reads as

## Related

- `SAIT-SMK-TPL-04-001A` — covers EXTEND/OVERRIDE directives, which are
  structural; a prose reference is checked by neither it nor TPL-06
- `SAIT-SMK-TPL-06-001A` — the same reachability question for directives
- Measured basis, 2026-09-01: 341 declared section IDs, 28 cross-file
  prose references across the tree, none dangling. The prefix pattern this
  check used until then saw 100 of those IDs and 14 of those references,
  and the two it missed in `base-typescript` dangled in three chains
