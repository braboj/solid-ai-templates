---
id: SAIT-E2E-STK-22-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567825
title: Full interview produces a correct CLAUDE.md for a C embedded project
product: sait
type: e2e
area: STK
priority: p1
status: ready
environment: [local]
automatable: yes
created: 2026-06-26
author: Branimir Georgiev
product-version: "2.x"
tags: [e2e, output, c, embedded]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/c-embedded.md` are attached to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` containing C/embedded-specific
> rules alongside base layer rules

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output contains embedded-specific rules (C17, CMake firmware/host targets, Unity host tests, cppcheck); base rules present |
| FAILED | Embedded-specific rules absent; output indistinguishable from a generic C project |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/c-embedded.md`, `base/core/agents.md`
3. Interview answers:
   - Project name: SensorFirmware
   - Target: STM32 (ARM Cortex-M4)
   - Toolchain: arm-none-eabi-gcc
   - Test runner: Unity (host build)
   - Output: CLAUDE.md (inline model)

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Stack` lists C17, CMake, Unity, cppcheck
2. Assert a `## C conventions` section is present
3. Assert firmware/host build separation referenced (cross-compile vs host)
4. Assert canonical sections present (Project structure, Commands)
5. Assert base git conventions present (`feat:`)

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-STK-15-001A`
