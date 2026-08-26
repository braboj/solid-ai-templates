---
id: SAIT-E2E-STK-12-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567830
title: Full interview produces a correct CLAUDE.md for a generic Python service
product: sait
type: e2e
area: STK
priority: p2
status: ready
environment: [local]
automatable: yes
created: 2026-03-22
author: Branimir Georgiev
product-version: "1.x"
tags: [e2e, output, python, service]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/python-service.md` are attached to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` containing the shared Python service
> rules that all Python stacks inherit from

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output contains shared Python service rules (virtual environment, type hints, Black/Ruff, pytest, logging); base rules present; no framework-specific rules present |
| FAILED | Framework-specific rules (Flask, FastAPI, Django) appear despite no framework being selected; shared rules absent |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/python-service.md`, `base/core/agents.md`
3. Interview answers:
   - Project name: DataPipelineWorker
   - Language: Python
   - Framework: none (plain Python service)
   - Output: CLAUDE.md

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Stack` lists Python with no web framework
2. Assert virtual environment conventions present (venv, `requirements.txt` or
   `pyproject.toml`)
3. Assert type hint rules present
4. Assert Black or Ruff referenced for formatting
5. Assert pytest referenced for testing
6. Assert no Flask, FastAPI, or Django rules present
7. Assert base git conventions present

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-STK-01-001A`, `SAIT-E2E-STK-11-001A`
