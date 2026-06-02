---
id: "001"
status: Accepted
date: 2025-03-01
category: composition
supersedes: []
superseded_by: []
---

# ADR-001: Inheritance model for template composition

## Context

AI context files (CLAUDE.md, AGENTS.md) contain rules that are largely
the same across projects using the same stack. Writing them from
scratch per project leads to inconsistency and drift. We needed a
system to define rules once and compose them for any project type.

## Decision

Use a three-layer inheritance model inspired by SOLID principles:

```
base/ → frontend/backend/ → stack/
```

- **base/** — cross-cutting rules (git, docs, quality, testing, security)
  that apply to every project regardless of stack
- **frontend/** and **backend/** — layer-specific rules that apply to
  all projects in that layer
- **stack/** — concrete, technology-specific rules that extend or
  override parent templates
- **platform/** — orthogonal to the chain; a project picks one
  platform (GitHub, GitLab) regardless of stack

Composition uses three directives:
- `[DEPENDS ON: ...]` — declares parent templates
- `[EXTEND: ...]` — adds rules to a parent section
- `[OVERRIDE: ...]` — replaces a parent section entirely

## Alternatives considered

1. **Monolithic templates** — one large file per stack with all rules
   inline. Rejected: duplicates base rules across 30+ stacks, making
   updates a maintenance nightmare.
2. **Copy-paste with manual sync** — share rules by copying. Rejected:
   drift is inevitable, no enforcement mechanism.
3. **Runtime includes** — tooling that merges files at build time.
   Rejected: adds complexity; agents can follow DEPENDS ON references
   natively without preprocessing.

## Consequences

- Adding a new base rule (e.g. a security convention) automatically
  applies to all stacks that depend on it
- Stack templates are small — they only contain what differs from
  the parent
- The dependency graph must be acyclic — enforced by smoke tests
- New contributors must understand the inheritance model before
  contributing (mitigated by ONBOARDING.md and SPEC.md)
