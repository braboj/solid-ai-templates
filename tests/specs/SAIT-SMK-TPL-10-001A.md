---
id: SAIT-SMK-TPL-10-001A
title: At most one OVERRIDE of an ID per resolved chain
product: sait
type: smoke
area: TPL
priority: p1
status: ready
environment: [local, ci]
automatable: yes
created: 2026-09-06
author: Branimir Georgiev
product-version: "2.x"
tags: [structure, composition, override, conflict]
---

## Short description

> **Given** every root a project can pick is resolved to its chain
> **When** the `[OVERRIDE: ...]` directives in that chain are collected
> **Then** no section ID is overridden by more than one template

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every overridden ID has exactly one overriding template per chain |
| FAILED | One or more IDs are overridden twice within a single chain |
| SKIPPED | — |
| BLOCKED | PyYAML is not installed |
| ERROR | The manifest cannot be read |

## Steps

### Prerequisites

- Repository cloned locally
- PyYAML installed

### Setup

1. Change to the repository root

### Execution

1. Resolve every stack root and every opt-in root from the manifest
2. For each chain, read every file it carries
3. Collect the target of every `[OVERRIDE: ...]` directive, keeping the
   file each came from
4. Group the targets by ID

### Assertions

1. Assert each overridden ID names exactly one file per chain

### Teardown

— (read-only check, no teardown required)

## Notes

`docs/SPEC.md` calls two templates overriding one ID an error the agent
MUST surface, and states no winner. Nothing reported it: `TPL-03`,
`TPL-04` and `TPL-06` check that a directive's target exists and is
reachable, not how many templates claim it.

A chain specialises across three levels without colliding by giving each
overriding section an `[ID:]` of its own and having the next level
override that — the pattern `go-lib` → `go-service` → `go-echo` uses.

Opt-in roots are resolved alongside stacks. A collision inside an opt-in
chain is invisible to a scan of stacks alone.

## Related

- Related procedures: `SAIT-SMK-TPL-04-001A`, `SAIT-INT-TPL-06-001A`,
  `SAIT-SMK-TPL-03-001A`
