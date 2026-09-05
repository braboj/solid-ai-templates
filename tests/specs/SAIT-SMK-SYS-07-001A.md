---
id: SAIT-SMK-SYS-07-001A
title: 360 audit reports live only under docs/audits/
product: sait
type: smoke
area: SYS
priority: p2
status: ready
environment: [local, ci]
automatable: yes
created: 2026-06-26
author: Branimir Georgiev
product-version: "2.x"
tags: [audit, 360, convention, adr-018]
---

## Short description

> **Given** the repository's files, ignored paths excluded
> **When** every Markdown file whose name matches a 360 audit report
> (`360-audit*.md` or `*-360.md`) is located
> **Then** each one lives under `docs/audits/` and uses the dated
> `YYYY-MM-DD-360.md` name — the single-file `docs/360-audit.md` form is
> never present

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every audit report is under `docs/audits/` with a dated `YYYY-MM-DD-360.md` name |
| FAILED | An audit report exists outside `docs/audits/`, or a file inside it uses a non-dated name |
| SKIPPED | — |
| BLOCKED | — |
| ERROR | File system is inaccessible, or `git ls-files` cannot run |

## Steps

### Prerequisites

- Repository cloned locally

### Setup

1. Change to the repository root

### Execution

1. List the repository's files with `git ls-files --cached --others
   --exclude-standard` — tracked files plus the untracked ones a commit
   could still add, with everything `.gitignore` excludes left out
2. Drop any path under a VCS or tooling directory (`.git`, `.venv`,
   `node_modules`, `__pycache__`, `.idea`, `.claude`)
3. Match each filename against the audit-report pattern
   (`360-audit*.md` or `*-360.md`)
4. For each match, record its path relative to the repository root

### Assertions

1. Assert no matched file lives outside `docs/audits/`
2. Assert every matched file under `docs/audits/` uses the
   `YYYY-MM-DD-360.md` dated-report name

### Teardown

— (read-only check, no teardown required)

## Related

- ADR-018 — `docs/audits/` is the sole audit-storage convention (the
  rule this check pairs with)
- `templates/base/workflow/360.md` [ID: 360-tracking] — the audit
  tracking rule
- `quality-gates-pair-check` — pair-the-check convention
