---
id: SAIT-SMK-SYS-16-001A
title: A stack category's context tier moves only on purpose
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
tags: [composition, context-window, readme, adoption]
---

## Short description

> **Given** a recorded context tier per stack category
> **When** each category's largest resolved chain is measured against the
> context windows a model actually sells
> **Then** a measured tier differing from the recorded one fails, because
> a crossing changes which models can run the stack at all and otherwise
> arrives as one changed word in a generated README table

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every category's measured tier equals its recorded one |
| FAILED | A category's measured tier differs from the record |
| FAILED | A measured category is absent from the record |
| FAILED | A recorded category is measured nowhere |
| FAILED | A category's chain exceeds every window a model sells |
| FAILED | The check measured no stacks or read no records |
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

1. Resolve and concatenate every stack's chain, and keep the largest per
   `layer` — the same quantity `README.md`'s model-limits table states
2. Convert to tokens and add the interview overhead, using `sync.py`'s
   own constants rather than a second copy of them
3. Take the smallest context window a model sells that still holds it
4. Compare against `tests/context-tiers.txt` in both directions of
   membership
5. Report the stacks measured, the categories measured and the
   categories recorded

### Assertions

1. Assert each category's measured tier equals its recorded tier
2. Assert the record and the measurement name the same categories, so a
   category cannot drop out of the record and stop being checked
3. Assert the counts are non-zero, per ADR-034

### Negative controls

Each control was observed failing, and each mutation was asserted to
have landed before its result was read.

1. **A crossing.** Appending 78,437 characters to `templates/stack/
   htmx.md` MUST fail. Observed 2026-09-06: `hypermedia` measured 399,383
   characters against a recorded 128K, and the check reported the
   category, both tiers and the stack carrying the largest chain
2. **A raise inside the tier.** Appending 11,237 characters to the same
   file MUST pass, since the chain stays under the 385,000 characters a
   128K window leaves after the interview. Observed 2026-09-06
3. **A category with no record.** Deleting the `hypermedia` line from
   `tests/context-tiers.txt` MUST fail. Observed 2026-09-06: the recorded
   count moved 6 → 5 and the check named the unrecorded category, so the
   corpus is confirmed to have changed rather than the message alone

## Related

- ADR-041 — chain size is reported, not capped. This check is the
  instrument that record names as the better one, and gates a different
  quantity: not what a rule costs the chain, but which models can still
  run the stack
- ADR-034 — why the counts are reported and floored

<!-- measured: 2026-09-06 -->

- Measured basis, 2026-09-06: 17 stacks across 6 categories. `embedded`
  and `hypermedia` sit at 128K, the other four at 200K. The nearest
  boundary is `hypermedia` at 320,946 characters against the 385,000 a
  128K window leaves, so an ordinary rule addition of that size crosses
  it

<!-- /measured -->
