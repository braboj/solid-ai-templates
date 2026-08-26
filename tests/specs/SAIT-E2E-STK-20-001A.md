---
id: SAIT-E2E-STK-20-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567838
title: Full interview produces a correct CLAUDE.md for an HTMX project
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
tags: [e2e, output, htmx, hypermedia, server-side]
---

## Short description

> **Given** `INTERVIEW.md` and `stack/htmx.md` are attached to an agent
> **When** the agent conducts the interview with a defined set of answers
> **Then** the agent produces a `CLAUDE.md` containing HTMX-specific rules
> alongside backend-templating and base rules

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output contains HTMX rules (hypermedia-first, hx-* attributes, partial HTML responses, OOB swaps); backend-templating and base rules present; no SPA or JSON API conventions present |
| FAILED | HTMX-specific rules absent; output resembles a JSON REST API or a JavaScript SPA |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/htmx.md`, `base/core/agents.md`
3. Interview answers:
   - Project name: AdminDashboard
   - Backend language: Python (Flask or FastAPI)
   - Templating engine: Jinja2
   - Progressive enhancement: Alpine.js for client-side state
   - Output: CLAUDE.md

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Stack` lists HTMX, Jinja2, and the chosen backend
2. Assert hypermedia-first principle documented (server returns HTML fragments, not
   JSON)
3. Assert `hx-*` attribute conventions present (`hx-get`, `hx-post`, `hx-target`,
   `hx-swap`)
4. Assert partial HTML response rules present (endpoints return fragments, not full
   pages)
5. Assert out-of-band (OOB) swap usage documented
6. Assert Alpine.js integration rules present if selected
7. Assert no JSON API or SPA routing conventions present
8. Assert base git conventions present

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-STK-11-001A`, `SAIT-E2E-STK-01-001A`
