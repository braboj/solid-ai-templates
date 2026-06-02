---
id: "002"
status: Accepted
date: 2026-04-28
category: process
supersedes: []
superseded_by: []
---

# ADR-002: Standardized issue labels across repositories

## Context

Imbra repositories used GitHub's default labels (enhancement, question,
documentation, good first issue, help wanted, invalid, wontfix) with
no consistency across repos. Labels had no priority dimension, making
triage by urgency impossible. Some labels were misleading (e.g.
`question` for spikes, `enhancement` for tasks).

## Decision

Standardize to 12 labels across all repositories, split into three
groups:

**Type labels (pick one per issue):**
`bug`, `epic`, `task`, `spike`, `incident`

**Priority labels (pick one per issue):**
`P0` (critical), `P1` (high), `P2` (medium), `P3` (low), `P4` (backlog)

**Triage labels (terminal — applied when closing):**
`duplicate`, `wontdo`

Rules:
- Every issue MUST have exactly one type + one priority
- Colors follow the Atlassian design system palette
- Type labels use saturated hues; priority labels use a warm-to-cool
  gradient to remain visually distinct when displayed side by side
- Issue types and priorities are platform-agnostic (base/issues.md);
  label names and colors are GitHub-specific (platform/github.md)

## Alternatives considered

1. **Keep GitHub defaults** — rejected: no priority dimension, labels
   like `enhancement` are verbose, `question` is misleading for spikes.
2. **Minimal set (bug + P0-P4 only)** — rejected: issue list becomes
   unreadable without type labels; you can't tell bugs from tasks at
   a glance.
3. **GitHub Projects custom fields** — rejected: requires a project
   board, fields not visible on the issue list, overhead for a solo
   project.

## Consequences

- Every issue in every Imbra repo has a complete type + priority
  matrix — no gaps when filtering or exporting
- Labels are documented in base/issues.md (types) and
  platform/github.md (implementation) — new repos get the same set
- Old labels (enhancement, question, documentation) were migrated
  and deleted — 55+ issues re-labeled with zero data loss
