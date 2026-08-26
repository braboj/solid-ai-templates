---
id: SAIT-E2E-STK-01-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567807
title: Full interview produces a correct CLAUDE.md for a Python FastAPI project
product: sait
type: e2e
area: STK
priority: p0
status: ready
environment: [local]
automatable: yes
created: 2026-03-22
author: Branimir Georgiev
product-version: "1.x"
tags: [e2e, output, fastapi, claude-md]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/python-fastapi.md` are attached to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` that contains all required sections
> with rules drawn from the correct templates in the dependency chain

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Generated `CLAUDE.md` contains all required sections; base rules and FastAPI-specific rules are both present; no section is empty or contradictory |
| FAILED | One or more required sections are missing; base rules absent; FastAPI-specific rules absent; sections are contradictory |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available
- Interview answers prepared (see Setup)

### Setup

1. Open Claude Code in any working directory
2. Attach the following files:
   - `INTERVIEW.md`
   - `stack/python-fastapi.md`
   - `base/core/agents.md`
3. Prepare the following interview answers:
   - **Project name**: OrderService
   - **Owner**: Platform team
   - **Repo**: github.com/acme/order-service
   - **Deployment**: Docker → Kubernetes (cloud)
   - **Database**: PostgreSQL via SQLAlchemy 2 + Alembic
   - **Auth**: JWT bearer tokens
   - **Feature flags**: no
   - **Messaging**: no
   - **Output format**: CLAUDE.md

### Execution

1. Ask the agent:
   ```
   Using INTERVIEW.md and stack/python-fastapi.md, generate a CLAUDE.md
   for this project. Use base/core/agents.md for formatting rules.
   ```
2. Provide the prepared interview answers when the agent asks
3. Save the generated output as `CLAUDE.md` in a temp directory

### Assertions

1. Assert the output contains all required top-level sections:
   - `## Stack`
   - `## Architecture`
   - `## Commands`
   - `## Git conventions`
   - `## Code conventions`
   - `## Testing`
2. Assert `## Stack` lists Python 3.11+, FastAPI, and SQLAlchemy
3. Assert `## Testing` references `pytest` and `pytest-asyncio`
4. Assert `## Code conventions` includes async handler rules (from `python-fastapi.md`)
5. Assert `## Code conventions` includes configuration rules (from `backend/config.md`)
6. Assert `## Git conventions` includes conventional commit prefixes (from
   `base/git.md`)
7. Assert no identity-level placeholders remain unsubstituted (e.g.
   `[your project]`, `[owner]`, `[repo]`); note that `[feature].py` in
   architecture diagrams is an intentional naming convention, not a
   placeholder

### Teardown

1. Delete the temporary `CLAUDE.md` generated during the test

## Related

- Related procedures: `SAIT-E2E-STK-02-001A`
- Implements: SPEC.md §How an agent uses the system
