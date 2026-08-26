---
id: SAIT-INT-TPL-02-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567804
title: EXTEND directive adds stack rules on top of parent section without removing base
rules
product: sait
type: int
area: TPL
priority: p1
status: ready
environment: [local]
automatable: yes
created: 2026-03-22
author: Branimir Georgiev
product-version: "1.x"
tags: [composition, extend, inheritance]
---

## Short description

> **Given** a stack template section marked `[EXTEND: <id>]` referencing a
> parent section tagged `[ID: <id>]`
> **When** an agent assembles the rule set for that section
> **Then** the output contains all rules from the parent section followed by
> all rules from the EXTEND section — no base rules are removed

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Assembled section contains all base rules AND all stack extension rules; order is base first, extension second |
| FAILED | One or more base rules are absent; or extension rules replace rather than extend base rules |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load or process the template files |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code or equivalent agent available
- Test pair: `base/testing.md` (contains `[ID: base-testing]`) and
  `stack/python-flask.md` (contains `[EXTEND: base-testing]` in its Testing section)

### Setup

1. Open Claude Code in the repository root
2. Attach `base/testing.md` and `stack/python-flask.md`

### Execution

1. Ask the agent:
   ```
   Show me the assembled Testing section for a Flask project.
   Include all rules from base/testing.md and all rules from the
   EXTEND in stack/python-flask.md.
   ```
2. Record the assembled output

### Assertions

1. Assert all rules from `base/testing.md` `[ID: base-testing]` are present
2. Assert all rules from `stack/python-flask.md` `[EXTEND: base-testing]`
   are present
3. Assert base rules appear before extension rules
4. Assert no base rule is missing or overwritten

### Teardown

— (read-only check, no teardown required)

## Related

- Related procedures: `SAIT-INT-TPL-01-001A`, `SAIT-INT-TPL-03-001A`
- Implements: SPEC.md §Override mechanism
