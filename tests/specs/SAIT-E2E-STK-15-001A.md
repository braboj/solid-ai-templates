---
id: SAIT-E2E-STK-15-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567833
title: Full interview produces a correct CLAUDE.md for a Python library project
product: sait
type: e2e
area: STK
priority: p1
status: ready
environment: [local]
automatable: yes
created: 2026-03-22
author: Branimir Georgiev
product-version: "1.x"
tags: [e2e, output, python, library]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/python-lib.md` are attached to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` containing Python library–specific rules
> without server or deployment sections

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output contains Python library rules (public API design, semver, pyproject.toml packaging, docstrings, no server entrypoint); base rules present |
| FAILED | Output includes server or deployment rules inappropriate for a library; packaging conventions absent |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/python-lib.md`, `base/core/agents.md`
3. Interview answers:
   - Project name: validify
   - Language: Python
   - Distribution: PyPI package
   - Output: CLAUDE.md

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Stack` lists Python with no framework
2. Assert `pyproject.toml` referenced for packaging metadata
3. Assert public API surface rules present (docstrings, type hints, backward
   compatibility)
4. Assert semantic versioning rules documented
5. Assert no Dockerfile or deployment section present
6. Assert base git conventions present

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-STK-12-001A`, `SAIT-E2E-STK-10-001A`
