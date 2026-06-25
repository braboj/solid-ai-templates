---
id: SAIT-SMK-SYS-05-001A
title: End-of-session audit is inlined verbatim or hard-delegated, never paraphrased
product: sait
type: smoke
area: SYS
priority: p1
status: ready
environment: [local, ci]
automatable: yes
created: 2026-06-25
author: Branimir Georgiev
product-version: "2.x"
tags: [generation, fidelity, session-protocol, output-spec]
---

## Short description

> **Given** the output spec (`agents.md`) and the example context files
> **When** the §6.3 end-of-session audit directive and every example
> session-protocol section are inspected
> **Then** each one inlines the `scope.md` audit verbatim or
> hard-delegates to it, keeping the enforcement phrase — none paraphrase
> the checklist into bullets

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every §6.3 directive and example session-protocol section keeps "execute each item" / "do not summarize" |
| FAILED | One or more paraphrase or soft-reference the audit, dropping the enforcement phrase |
| SKIPPED | — |
| BLOCKED | — |
| ERROR | File system is inaccessible |

## Steps

### Prerequisites

- Repository cloned locally

### Setup

1. Change to the repository root
2. Read `templates/base/core/agents.md`
3. Read every `examples/*/CLAUDE.md`

### Execution

1. For each `### 6.3` directive in `agents.md`, capture the directive
   block up to the next heading or code fence
2. For each example with a `Session protocol` / `End of session`
   heading, capture the section up to the next top-level heading
3. Match each captured block against the enforcement signature
   (`execute each item` / `do not summari[sz]e` / `do not paraphrase`)

### Assertions

1. Assert every `agents.md` §6.3 directive matches the signature
2. Assert every example session-protocol section matches the signature
3. Examples with no session-protocol section are out of scope (skipped)

### Teardown

— (read-only check, no teardown required)

## Related

- Issue #498 — generation drops/condenses the end-of-session audit
- `quality-gates-pair-check` — the rule this check pairs with
- `templates/base/workflow/scope.md` — canonical End of session audit
