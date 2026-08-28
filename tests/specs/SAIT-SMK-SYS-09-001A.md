---
id: SAIT-SMK-SYS-09-001A
title: sync.py --check inspects without writing
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
tags: [tooling, staleness-gate, check-timing]
---

## Short description

> **Given** a file holding a stale generated block
> **When** `_update_file` is called in check mode and then in plain mode
> **Then** check mode reports the difference and leaves the bytes
> untouched, while plain mode writes — a gate that repairs what it
> inspects reports clean on its second run, so only its first
> invocation would carry information

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Check mode reports the difference, the file is byte-identical afterwards, and plain mode writes |
| FAILED | Check mode wrote to the file, missed the difference, or plain mode did not write |
| SKIPPED | — |
| BLOCKED | — |
| ERROR | `tools/sync.py` cannot be imported |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3

### Setup

1. Create a temporary directory
2. Write a file containing one `generated:` marker pair around stale
   content

### Execution

1. Call `_update_file(target, {marker: "FRESH"}, True)` and read the file
   back
2. Rewrite the stale file and call `_update_file(target, {marker:
   "FRESH"})` without check mode

### Assertions

1. Assert check mode returned that the file differs
2. Assert the file is byte-identical to what was written before the call
3. Assert plain mode wrote the fresh content — without this, a function
   that did nothing at all would satisfy assertion 2

### Teardown

— (the temporary directory is removed by its context manager)

## Related

- `quality-gates-check-timing` — a check that alters its own subject is
  honest only on its first invocation (the rule this check guards)
- `quality-gates-staleness` — the gate whose `--check` convention this
  tool implements
- `SAIT-SMK-SYS-08-001A` — sibling structural check on committed
  artifacts
