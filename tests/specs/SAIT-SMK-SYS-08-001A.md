---
id: SAIT-SMK-SYS-08-001A
title: Every showcased stack keeps its example CLAUDE.md
product: sait
type: smoke
area: SYS
priority: p2
status: ready
environment: [local, ci]
automatable: yes
created: 2026-06-26
author: Branimir Georgiev
product-version: "2.x"
tags: [examples, adr-016, convention]
---

## Short description

> **Given** the committed example->stack mapping (`REQUIRED_EXAMPLES`)
> **When** each required example directory is checked
> **Then** every example has a non-empty `CLAUDE.md` and the stack it
> demonstrates exists in the manifest — a showcased example cannot be
> silently removed, emptied, or pointed at a deleted stack

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every required example has a non-empty CLAUDE.md and maps to a stack present in the manifest |
| FAILED | A required example's CLAUDE.md is missing or empty, or its mapped stack is not in the manifest |
| SKIPPED | PyYAML is not installed |
| BLOCKED | — |
| ERROR | File system is inaccessible |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3 with PyYAML installed

### Setup

1. Change to the repository root

### Execution

1. Load `manifest.yaml` and collect the declared stack IDs
2. For each `REQUIRED_EXAMPLES` entry (example directory -> stack ID),
   resolve `examples/<dir>/CLAUDE.md`
3. Record missing/empty files and mapped stacks absent from the manifest

### Assertions

1. Assert every required `examples/<dir>/CLAUDE.md` exists and is non-empty
2. Assert every mapped stack ID is present in the manifest

### Teardown

— (read-only check, no teardown required)

## Related

- ADR-016 — examples are agent-generated, regenerated on material change
  (the rule this check guards)
- `SAIT-SMK-SYS-05-001A` — validates the audit rendering of examples
  that exist; this check guards their existence
- `quality-gates-pair-check` — pair-the-check convention
