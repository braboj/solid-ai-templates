---
id: SAIT-E2E-STK-07-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567822
title: Full interview produces a correct CLAUDE.md for an Astro static site project
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
tags: [e2e, output, astro, static-site]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/static-site-astro.md` are attached to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` containing Astro-specific rules
> alongside frontend layer and base rules

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output contains Astro-specific rules (content collections, islands, zero-JS default, MDX); frontend and base rules present |
| FAILED | Astro-specific rules absent; output resembles a React SPA or generic frontend project |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/static-site-astro.md`, `base/core/agents.md`
3. Interview answers:
   - Project name: TechBlog
   - Language: TypeScript
   - Content: Markdown + MDX
   - Integrations: React islands for interactive components
   - Output: CLAUDE.md

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Stack` lists Astro, TypeScript, MDX
2. Assert content collections rules present (typed schemas, `src/content/`)
3. Assert zero-JS default principle documented (opt-in via `client:*` directives)
4. Assert island hydration directives referenced (`client:load`, `client:idle`, etc.)
5. Assert build output targets static (`output: 'static'` or equivalent)
6. Assert base git conventions present

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-STK-20-001A`