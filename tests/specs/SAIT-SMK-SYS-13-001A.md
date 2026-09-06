---
id: SAIT-SMK-SYS-13-001A
title: The instructed manual walk reaches what the resolver carries
product: sait
type: smoke
area: SYS
priority: p1
status: ready
environment: [local, ci]
automatable: yes
created: 2026-09-03
author: Branimir Georgiev
product-version: "2.x"
tags: [composition, adoption, readme, resolver-parity]
---

## Short description

> **Given** a README that instructs an adopter without shell access to
> build a context file by reading the manifest and walking DEPENDS ON
> **When** that walk is performed for every root a project can pick and
> compared against what the resolver produces for the same root
> **Then** a file the resolver carries that the walk cannot reach fails,
> because an adopter following the instruction loses whole rules and gets
> no error — nothing declares what is absent

## Results

| Result | Condition |
|--------|-----------|
| PASSED | For every root, the instructed walk and the resolved chain hold the same files |
| FAILED | The resolver carries a file the instructed walk cannot reach |
| FAILED | The instructed walk reaches a file the resolver does not carry |
| FAILED | README no longer tells the manual path to load the manifest's `core:` list |
| FAILED | The check compared no roots, or the core tier is empty |
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

1. Read the core tier from the manifest — the files the resolver seeds
   into every chain regardless of what any template declares
2. Enumerate every root a project can pick: each stack, and each
   orthogonal template that resolves as its own root
3. For each root, walk `[DEPENDS ON:]` transitively from the root's own
   file. The directives are read out of the files rather than from the
   manifest's `depends_on`, because a reader following the README has
   only the files
4. Union that walk with the core tier — this is what the README's
   instruction produces when followed exactly
5. Compare it against the resolved chain in both directions of
   membership
6. Assert README still instructs the core-tier load, since the
   instruction is half of the pair under test
7. Report the core-tier size, the stacks and opt-in roots compared as
   two counts, and how many files the
   DEPENDS ON walk alone would miss summed over roots

### Assertions

1. Assert no file is in the resolved chain and outside the instructed
   walk — that is a rule the adopter silently loses
2. Assert no file is in the instructed walk and outside the resolved
   chain — that is an instruction that overshoots the chain
3. Assert README names the manifest's `core:` list, so this check cannot
   keep passing against a document that stopped saying to seed it
4. Assert the root count and the core-tier count are non-zero, per
   ADR-034: a check that compared nothing reports what parity reports

### Negative controls

Each control was observed failing, and each mutation was asserted to
have landed before its result was read.

1. **README stops naming the core tier.** Removing the `core:` clause
   from the quick-start prompt MUST fail. Observed 2026-09-03:
   occurrences of `core:` went 1 → 0 and the check failed naming the
   document
2. **The resolver carries a file the walk cannot reach.** Adding
   `base-agents` to `stack-htmx`'s manifest `depends_on` without the
   matching directive in `htmx.md` MUST fail. Observed 2026-09-03: the
   check named `templates/base/core/agents.md` under `stack-htmx`. The
   control asserts the mutated manifest still *parses* and that the edge
   is in the parsed data — a corrupt file makes the check error, which is
   not the failure being tested
3. **The walk overshoots the chain.** Appending
   `templates/base/core/agents.md` to `htmx.md`'s `[DEPENDS ON:]`
   directive without the manifest edge MUST fail in the other direction.
   Observed 2026-09-03, naming the same file with the opposite message
4. A first attempt at control 2 matched a byte pattern containing `\n`
   against a working copy carrying CRLF. It edited nothing, and the check
   then reported PASS — the guard reading as held when it had never been
   exercised. Match by line, or normalise first

## Related

- `SAIT-SMK-MNF-02-001A` — that every stack resolves at all; this check
  is about whether a human following the documented path reproduces it
- `SAIT-SMK-SYS-04-001A` — that DEPENDS ON headers match the manifest's
  `depends_on`; that parity is between two machine-readable forms, this
  one is between the instruction and the resolver
- ADR-035 — why the corpus is every root and not the stacks alone
- ADR-034 — why the counts are reported and floored
<!-- measured: 2026-09-03 -->

- Measured basis, 2026-09-03: 6 core-tier files, 37 roots, and 148 files
  the DEPENDS ON walk alone would miss summed over roots. Before the
  README was corrected, `templates/base/core/readme.md` and
  `templates/base/core/review.md` were missed by 17 of 17 stacks, so the
  documented manual path lost the code-review rules on every chain

<!-- /measured -->
