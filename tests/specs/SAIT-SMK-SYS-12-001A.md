---
id: SAIT-SMK-SYS-12-001A
title: No resolved chain exceeds its recorded ceiling
product: sait
type: smoke
area: SYS
priority: p1
status: ready
environment: [local, ci]
automatable: yes
created: 2026-09-01
author: Branimir Georgiev
product-version: "2.x"
tags: [composition, reach, context-cost, ratchet]
---

## Short description

> **Given** a repository whose template corpus grows inside the files
> every chain already carries
> **When** each root a project can pick is resolved and its chain
> measured against the ceiling recorded for it
> **Then** a chain over its ceiling fails, so raising the ceiling is a
> deliberate line in the same change and the diff states what the
> addition costs every project on that chain

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every root resolves within its recorded ceiling, and every root has one |
| FAILED | A chain exceeds its ceiling, a root has no ceiling, or a ceiling names a root that no longer resolves |
| FAILED | The check resolved no roots, or the budget file records no ceilings |
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

1. Resolve every root: each stack, and each orthogonal template a project
   opts into as its own root per ADR-035. Stacks alone leave every opt-in
   root uncapped
2. Measure each chain as the decoded character count of its resolved
   files. Text mode makes a CRLF working copy and an LF one measure the
   same tree the same; a byte count would tie every ceiling to the
   platform that recorded it
3. Read the ceilings from `tests/chain-budget.txt`
4. Compare each measured chain against its ceiling, in both directions of
   membership
5. Report the stacks measured and the opt-in roots measured as two
   counts, the ceilings recorded, the largest chain
   and the tightest headroom

### Assertions

1. Assert no chain exceeds its ceiling, naming the overage and the file
   to edit
2. Assert every measured root has a ceiling — a new stack that arrives
   without one would otherwise grow unmeasured
3. Assert every ceiling names a root that still resolves, so a rename
   leaves a failing entry rather than a silently dead one
4. Assert the root count and the ceiling count are non-zero, per ADR-034:
   a check that measured nothing reports what a clean tree reports

### Negative controls

1. Append a rule to a file resolving into every chain; the check MUST
   fail and name every root carrying it. Observed 2026-09-01: 47
   characters added to `base/core/quality.md` failed every root
2. Delete one ceiling; the check MUST fail on that root as unmeasured and
   print the exact line to restore
3. Record a ceiling for a root that does not resolve; the check MUST fail
   it as stale
4. Each control MUST be observed failing, and the mutation MUST be
   asserted before its result is read — a pattern that edits nothing
   leaves the tree clean and the check green, which reads as the guard
   holding when it never ran

## Related

- `SAIT-SMK-MNF-02-001A` — that every stack resolves at all; this check
  is about what the resolution costs
- ADR-035 — why the corpus is every root and not the stacks alone
- ADR-034 — why the counts are reported and floored
<!-- measured: 2026-09-01 -->

- Measured basis, 2026-09-01: 37 roots (17 stacks, 20 orthogonal), the
  largest chain `stack-django` at 453,564 characters. The corpus went
  from 387KB and 359 RFC-2119 occurrences at v2.1.0 to 782KB and 858 at
  v2.72.0 with the file count flat, and `sync.py --check` reported the
  size on every run without ever refusing it

<!-- /measured -->
