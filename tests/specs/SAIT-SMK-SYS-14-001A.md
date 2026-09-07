---
id: SAIT-SMK-SYS-14-001A
title: resolve.py accounts for every argument it is given
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
tags: [tooling, resolver, cli, composition]
---

## Short description

> **Given** a resolver invoked with roots and flags from a command line
> **When** each invocation's exit status and message are compared against
> what that invocation should produce
> **Then** an argument the resolver silently drops fails, because a root
> that does not exist otherwise passes whenever it follows a valid one
> and the wrong chain resolves at exit 0

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every case exits as expected and its message carries the phrase that identifies the reason |
| FAILED | A case exits with an unexpected status |
| FAILED | A case exits as expected and its message does not carry the phrase, so the status may be right for the wrong reason |
| FAILED | The check read no cases |
| SKIPPED | — |
| BLOCKED | — |
| ERROR | — |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3

### Setup

— (operates on the committed tree)

### Execution

1. Run `tools/resolve.py` once per case in `RESOLVE_CASES`, capturing
   status, stdout and stderr
2. Compare the status against the case's expectation
3. Where the case names a phrase, assert it appears in the combined
   output
4. Report how many argument cases were exercised

### Assertions

1. Assert a single valid root resolves at status 0
2. Assert an unknown root fails and says so — `Unknown stack ID`
3. Assert two roots are refused rather than concatenated, and say why —
   `Roots resolve independently`. Roots do not compose: per ADR-035 a
   stack and an orthogonal template each resolve as their own root
4. Assert an unknown flag fails with `Unknown flag`
5. Assert a bare invocation is the usage path rather than an error,
   matching the behaviour of a help flag
6. Assert the case count is non-zero, per ADR-034

Each case asserts the status **and** a phrase from the message, because a
program that exits 1 for the wrong reason reads identical to one that
exits 1 for the right one.

### Negative controls

1. **The defect that motivated the check.** The resolver took the first
   argument and ignored the rest, so `resolve.py <valid-root>
   <missing-root>` exited 0 having resolved a chain the caller did not
   ask for. The two-root case fails against that behaviour
2. **A status right for the wrong reason.** A build failing on an
   unrelated error also exits 1 for the unknown-root case; the phrase
   assertion is what separates the two

## Related

- ADR-035 — a platform template resolves as its own root, which is why
  more than one root is refused rather than concatenated
- ADR-034 — why the case count is reported and floored
