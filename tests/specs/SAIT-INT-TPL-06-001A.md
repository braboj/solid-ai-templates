---
id: SAIT-INT-TPL-06-001A
title: EXTEND and OVERRIDE targets are reachable in the resolved chain
product: sait
type: integration
area: TPL
priority: p1
status: ready
environment: [local, ci]
automatable: yes
created: 2026-05-06
author: Branimir Georgiev
product-version: "2.x"
tags: [chain, extend, override, reachability]
---

## Short description

> **Given** the manifest is loaded and every root a project can pick is
> resolved — each stack, and each orthogonal template a project opts into
> independently of its stack
> **When** every `[EXTEND: <id>]` and `[OVERRIDE: <id>]` directive in every
> file of a root's resolved chain is collected
> **Then** each referenced ID matches an `[ID: <id>]` tag declared in a file
> that is also part of that same resolved chain

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every EXTEND/OVERRIDE target in every chain file is declared by another file in the same chain |
| FAILED | One or more targets reference an ID declared in a file outside the resolved chain |
| FAILED | Either corpus is empty — no stacks resolved, or no opt-in roots resolved |
| SKIPPED | PyYAML not installed |
| BLOCKED | `SAIT-INT-MNF-02-001A` is failing |
| ERROR | File system or manifest is inaccessible |

## Steps

### Prerequisites

- Repository cloned locally
- `pyyaml` installed (`pip install pyyaml`)

### Setup

1. Load `templates/manifest.yaml`
2. Resolve the dependency chain for every stack entry
3. Resolve the dependency chain for every entry no stack chain reaches —
   the extras and platform templates a project opts into. These are
   picked independently of the stack, so what guarantees their target is
   their own chain: the core tier plus their `depends_on` tree

### Execution

1. For each root, collect all `[ID: X]` declarations from every
   file in its resolved chain into a set `chain_ids`
2. For each file in the chain, collect all `[EXTEND: X]` and
   `[OVERRIDE: X]` references
3. For each reference, check that the target ID is in `chain_ids`

### Assertions

1. Assert every EXTEND/OVERRIDE target is present in the chain's
   collected IDs
2. Assert both corpora are non-empty, and report each count separately —
   an opt-in corpus that empties leaves the orthogonal templates
   unexamined while the stack count keeps the check looking busy

### Negative controls

1. Remove `base-issues` from `platform-linear`'s `depends_on`; the check
   MUST report the `[EXTEND: base-issues-types]` in `platform/linear.md`
   as unreachable. Under a stack-only corpus it reported nothing: the
   file sits in no stack chain, and both platform templates extended a
   section one chain in seventeen carries

### Teardown

None.

## Related

- Supersedes gap in: `SAIT-SMK-TPL-04-001A` (checks global existence only)
- Depends on: `SAIT-INT-MNF-02-001A` (chains must resolve first)
- `SAIT-SMK-SYS-11-001A` — the same reachability question for a section
  named in running prose rather than by a directive
- Context: issue #283, discovered via #276
- Measured basis, 2026-09-01: 218 directives across 37 roots — 17 stacks
  and 20 orthogonal templates
