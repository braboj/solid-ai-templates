---
id: SAIT-SMK-SYS-06-001A
title: Every usable stack's resolved chain carries the MUST sections
product: sait
type: smoke
area: SYS
priority: p1
status: ready
environment: [local, ci]
automatable: yes
created: 2026-06-26
author: Branimir Georgiev
product-version: "2.x"
tags: [stack, structure, sections, adr-017]
---

## Short description

> **Given** the manifest and every stack's resolved dependency chain
> **When** each stack chain is inspected for the ADR-017 MUST-tier
> sections
> **Then** every chain contains `## Stack`, `## Commands`, and
> `## Project structure` — except pure-library stacks (layer: library),
> which are exempt from Project structure

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every stack chain carries Stack, Commands, and Project structure (libraries exempt from the last) |
| FAILED | One or more chains miss a required MUST section |
| SKIPPED | — |
| BLOCKED | PyYAML is not installed |
| ERROR | File system is inaccessible |

## Steps

### Prerequisites

- Repository cloned locally
- PyYAML installed (`py -m pip install pyyaml`)

### Setup

1. Change to the repository root
2. Load `templates/manifest.yaml`

### Execution

1. Enumerate every entry whose file is under `templates/stack/`
2. Resolve each stack's full dependency chain (core tier + parents)
3. Concatenate the chain's file contents
4. For each MUST section, search the concatenated text for the exact
   heading (`^## <Section>$`)

### Assertions

1. Assert `## Stack` is present in every stack chain
2. Assert `## Commands` is present in every stack chain
3. Assert `## Project structure` is present, except where the stack's
   manifest `layer` is `library`

### Teardown

— (read-only check, no teardown required)

## Related

- ADR-017 — canonical stack-template section structure (the rule this
  check pairs with)
- Issue #641 — implement the SYS-06 gate
- `quality-gates-pair-check` — pair-the-check convention
