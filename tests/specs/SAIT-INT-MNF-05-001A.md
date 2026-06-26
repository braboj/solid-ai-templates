---
id: SAIT-INT-MNF-05-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567823
title: resolve.py resolution matches the PyYAML resolution
product: sait
type: int
area: MANIF
priority: p0
status: ready
environment: [local, ci]
automatable: yes
created: 2026-06-26
author: Branimir Georgiev
product-version: "2.x"
tags: [manifest, resolution, parser-parity]
---

## Short description

> **Given** the repository is cloned and `manifest.yaml` is present
> **When** every stack is resolved with both the stdlib-only parser in
> `tools/resolve.py` and the PyYAML-based parser used by smoke
> **Then** the two ordered file chains are identical for every stack

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Both parsers produce the same ordered file chain for every stack |
| FAILED | One or more stacks resolve to different chains between the two parsers |
| SKIPPED | `manifest.yaml` is absent or PyYAML is not installed |
| BLOCKED | `SAIT-INT-MNF-02-001A` is failing |
| ERROR | `tools/resolve.py` cannot be imported; file system is inaccessible |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3 with PyYAML installed

### Execution

1. Load `manifest.yaml` with the hand-rolled parser in
   `tools/resolve.py` and resolve each stack's chain
2. Load `manifest.yaml` with `yaml.safe_load` and resolve each stack's
   chain with the same algorithm
3. Compare the two ordered file lists per stack

### Assertions

1. Assert each stack's `resolve.py` chain equals its PyYAML chain,
   element-for-element and in order

### Teardown

— (read-only check, no teardown required)

## Related

- Related procedures: `SAIT-INT-MNF-02-001A`, `SAIT-INT-MNF-04-001A`
- Implements: closes the divergent-parser gap behind #654 (#655)
