---
id: SAIT-SMK-SYS-02-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567802
title: All section IDs are unique across all templates
product: sait
type: smoke
area: SYS
priority: p0
status: ready
environment: [local, ci]
automatable: yes
created: 2026-03-22
author: Branimir Georgiev
product-version: "1.x"
tags: [structure, ids, uniqueness]
---

## Short description

> **Given** the repository is cloned and all template files are present
> **When** all `[ID: ...]` declarations across every template file are
> collected — a declaration is an `[ID: ...]` tag that is the entire
> content of its line (whitespace-only surroundings allowed); inline
> occurrences in prose, code spans, or table cells are references, not
> declarations
> **Then** no two declarations share the same ID value

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every sole-line `[ID: ...]` declaration is unique across all files in `base/`, `backend/`, `frontend/`, and `stack/` |
| FAILED | Two or more templates declare the same `[ID: ...]` value on a sole line |
| SKIPPED | Repository cannot be cloned or accessed |
| BLOCKED | — |
| ERROR | File system is inaccessible; `grep` or equivalent tool fails |

## Steps

### Prerequisites

- Repository cloned locally
- Shell access with `grep` and `sort` available

### Setup

1. Change to the repository root

### Execution

1. Extract all sole-line `[ID: ...]` declarations from every template
   file — a line matches when stripping leading/trailing whitespace
   leaves only the `[ID: ...]` tag:
   ```bash
   grep -rhE "^[[:space:]]*\[ID:[^]]+\][[:space:]]*$" \
     base/ backend/ frontend/ stack/ | sort
   ```
2. Identify duplicates:
   ```bash
   grep -rhE "^[[:space:]]*\[ID:[^]]+\][[:space:]]*$" \
     base/ backend/ frontend/ stack/ | sort | uniq -d
   ```

Inline references to existing IDs in prose (e.g. "see the
`[ID: base-ai-workflow]` section") are not declarations and MUST NOT
appear in the duplicate set.

### Assertions

1. Assert the output of the duplicate check is empty — no duplicates exist
2. Assert every `[EXTEND: <id>]` and `[OVERRIDE: <id>]` reference matches
   an `[ID: ...]` that exists somewhere in the template tree

### Teardown

— (read-only check, no teardown required)

## Notes

Semi-manual because cross-file ID resolution requires a script.
A future CI step should automate this using `manifest.yaml`.

## Related

- Related procedures: `SAIT-SMK-SYS-01-001A`, `SAIT-INT-TPL-02-001A`, `SAIT-INT-TPL-03-001A`