---
id: SAIT-E2E-STK-23-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567826
title: Full interview produces a correct CLAUDE.md for a tutorial site project
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
tags: [e2e, output, astro, tutorial]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/static-site-tutorial.md` are attached
> to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` containing tutorial-site rules
> (chapter content layer) on top of the Astro static-site rules

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output contains tutorial-specific rules (chapters/ content layer, chapter structure with Exercises/Quiz) on top of Astro static-site rules |
| FAILED | Tutorial-specific rules absent; output indistinguishable from a plain Astro static site |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/static-site-tutorial.md`,
   `base/core/agents.md`
3. Interview answers:
   - Project name: LearnAstro
   - Content: Multi-chapter Markdown in chapters/
   - Diagrams: Mermaid
   - Output: CLAUDE.md (inline model)

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert Astro static-site rules are present (inherited from the chain)
2. Assert the `chapters/` content layer is described
3. Assert the chapter structure references Exercises and Quiz
4. Assert canonical Commands section present
5. Assert base git conventions present (`feat:`)

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-STK-07-001A`
