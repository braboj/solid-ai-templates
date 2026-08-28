---
id: SAIT-SMK-SYS-10-001A
title: A quoted DEPENDS ON in prose is not a declaration
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
tags: [parser, depends-on, composition]
---

## Short description

> **Given** a synthetic template holding a header declaration, a
> backticked directive in body prose, and a fenced one
> **When** the header extraction runs over it
> **Then** only the header declaration is returned — a section that
> quotes the directive syntax to explain the composition model is
> documentation, and reading it as a declaration fails the tree against
> a file nobody wrote

## Results

| Result | Condition |
|--------|-----------|
| PASSED | The extraction returns exactly the header's declared path |
| FAILED | It returns a backticked or fenced occurrence, or misses the header |
| SKIPPED | — |
| BLOCKED | — |
| ERROR | — |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3

### Setup

— (the document under test is built in the check)

### Execution

1. Build a document with a header declaration, a backticked directive in
   prose after the first section heading, and a fenced one
2. Call the header extraction on it

### Assertions

1. Assert the result is exactly the header's declared path — this covers
   both directions at once, since a result that is too wide includes the
   quoted occurrences and one that is too narrow drops the header

## Related

- `SAIT-SMK-SYS-01-001A` — resolves the declared paths this extraction
  returns
- `SAIT-SMK-SYS-04-001A` — compares the same extraction against the
  manifest
- Measured basis: every DEPENDS ON declaration in the tree sits on line
  2, 3 or 4, before the first `## ` heading, across all template files
