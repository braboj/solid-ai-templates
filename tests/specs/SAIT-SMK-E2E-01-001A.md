---
id: SAIT-SMK-E2E-01-001A
title: All cases.py paths resolve to existing files
product: sait
type: smoke
area: E2E
priority: p2
status: ready
environment: [local, ci]
automatable: yes
created: 2026-09-07
author: Branimir Georgiev
product-version: "2.x"
tags: [tests, e2e, fixtures, references]
---

## Short description

> **Given** an end-to-end suite whose cases name the template files each
> run attaches to an agent
> **When** every named path is resolved against the tree without calling
> a model
> **Then** a case naming a file that has moved fails here, because the
> live suite needs an API key and a renamed template would otherwise
> surface only as a confusing model answer

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every non-skipped case carries the required fields and every path it names exists and is non-empty |
| FAILED | A case is missing a required field, or its `required` list is empty |
| FAILED | A case names a stack file that is absent or empty |
| FAILED | A case names an absent `output_file` or `extra_files` entry |
| FAILED | `templates/INTERVIEW.md` is absent |
| FAILED | The check validated no cases |
| SKIPPED | — |
| BLOCKED | — |
| ERROR | — |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3

### Setup

— (operates on the committed tree; no API key and no model call)

### Execution

1. Confirm `templates/INTERVIEW.md` exists, since every case attaches it
2. For each case in `cases.py` that is not marked skipped, check the
   required fields are present and the `required` list is non-empty
3. Resolve the `stack`, `output_file` and `extra_files` paths against the
   tree
4. Report how many cases were defined and how many were validated

### Assertions

1. Assert every required field is present on every validated case
2. Assert each named path exists, and that a stack file is non-empty —
   an empty template resolves and teaches the agent nothing
3. Assert the validated count is non-zero, per ADR-034. The defined and
   validated counts differ by the skipped cases, so reporting both is
   what makes a growing skip list visible

### Negative controls

1. **A moved template.** Renaming a file a case names MUST fail here,
   which is the whole point of running it without a model: the live
   suite runs only on the cadence the PLAYBOOK states (#1368), so between
   live runs this check is the only thing reading those paths
2. **An empty stack file.** Truncating a named stack to zero bytes MUST
   fail, since existence alone would pass while the case teaches nothing

## Related

- ADR-034 — why the counts are reported and floored
- `tests/CODIFICATION.md` — the ID scheme these case identifiers follow
