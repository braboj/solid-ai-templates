---
id: SAIT-E2E-STK-10-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567825
title: Full interview produces a correct CLAUDE.md for a Go library project
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
tags: [e2e, output, go, library]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/go-lib.md` are attached to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` containing Go library–specific rules
> without server or deployment sections

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output contains Go library rules (exported API design, semver, no main package, godoc); server/deployment sections absent; base rules present |
| FAILED | Output includes server or deployment rules inappropriate for a library; library API conventions absent |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/go-lib.md`, `base/core/agents.md`
3. Interview answers:
   - Project name: retrykit
   - Language: Go
   - Distribution: Go module (pkg.go.dev)
   - Output: CLAUDE.md

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Stack` lists Go (no framework)
2. Assert exported API design rules present (godoc, backward compatibility, minimal
   surface)
3. Assert semantic versioning rules documented
4. Assert no `main` package guidance (library only)
5. Assert no Dockerfile or deployment section present in the output
6. Assert base git conventions present

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-STK-08-001A`
