---
id: SAIT-E2E-STK-21-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567824
title: Full interview produces a correct CLAUDE.md for a NestJS project
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
tags: [e2e, output, nestjs, nodejs]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/node-nestjs.md` are attached to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` containing NestJS-specific rules
> alongside base and backend layer rules

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output contains NestJS-specific rules (modules/providers, class-validator, Jest + Supertest); base and backend rules present |
| FAILED | NestJS-specific rules absent; output indistinguishable from a generic Node backend |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/node-nestjs.md`, `base/core/agents.md`
3. Interview answers:
   - Project name: PaymentsAPI
   - Language: TypeScript
   - HTTP adapter: Express
   - ORM: Prisma
   - Auth: JWT
   - Output: CLAUDE.md (inline model)

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Stack` lists NestJS, TypeScript, class-validator
2. Assert validation rules reference class-validator / class-transformer
3. Assert Jest referenced in the testing section
4. Assert canonical sections present (Project structure, Commands)
5. Assert base git conventions present (`feat:`)

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-STK-04-001A`
