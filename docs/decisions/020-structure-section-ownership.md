---
id: "020"
status: Accepted
date: 2026-07-05
category: templates
supersedes: []
superseded_by: []
---

# ADR-020: README owns the directory map

## Context

Two rules were in tension over who owns the "Project structure"
section. The documentation standard declares `README.md` the single
source of truth for project structure and forbids duplicating it in
other documents. The canonical section structure for generated agent
context files requires a Project structure section in every
`CLAUDE.md` / `AGENTS.md`.

A generated context file that satisfies the second rule with a
directory tree violates the first, and the two copies drift. Observed
downstream (demo-sensor-app): README and CLAUDE.md both carried a
tree; the CLAUDE.md copy went stale — it labelled generated files
"(to generate)" and missed later-added directories — while the README
stayed current.

## Decision

1. **README owns the directory map** — the README "Project structure"
   section is the only rendered directory map in a project. No other
   document carries a second one.
2. **The generated section is a pointer plus rules** — the Project
   structure section of a generated `CLAUDE.md` / `AGENTS.md` MUST
   reference the README "Project structure" section and MAY add
   agent-facing placement rules (what belongs where, per-file content
   requirements). It MUST NOT contain a second directory tree.
3. **Stack templates keep their layout sections** — a stack template's
   Project structure section describes the recommended layout for a
   new project. It is generation-time input (it seeds the README and
   scaffolding), not live project state, so it does not violate the
   single-source-of-truth rule.

## Alternatives considered

- **Drop the Project-structure requirement from generated files** —
  rejected; agents lose placement guidance and the section role
  numbering stays fixed regardless.
- **Keep both trees, add a non-drift rule (CLAUDE.md tree generated
  from README)** — rejected; requires tooling no consumer project
  has, and drift returns between regenerations.
- **Placement rules only, without the README pointer** — rejected;
  the agent is left without the location of the authoritative map.

## Consequences

- `templates/base/core/docs.md` "Single source of truth" names the
  pointer-plus-rules pattern for agent context files.
- `templates/base/core/agents.md` skeleton placeholders for section
  1.2 are updated in all three models; the hybrid "what to inline"
  entry scopes Project structure to placement rules.
- Existing `examples/*/CLAUDE.md` still show inline trees. They are
  standalone previews with no adjacent README to point at; they get
  realigned at the next pipeline regeneration.
- Downstream projects reduce their context-file structure sections to
  a pointer plus placement rules.

## Related

- `templates/base/core/docs.md` — single source of truth section
- `templates/base/core/agents.md` — output skeletons
- ADR-017 — canonical stack-template section structure (context only)
