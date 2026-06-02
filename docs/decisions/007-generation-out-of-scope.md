---
id: 007
status: Accepted
date: 2026-05-06
category: tooling
supersedes: []
superseded_by: []
---

# ADR-007: Generation is out of scope

## Context

During e2e testing of the generation flow (session 2026-05-05,
PR #235), we discovered several issues with API-based generation:

- Models summarize, truncate, and miss details when generating
  from large prompts
- Backend stacks produce prompts of 24-50K tokens, which degrades
  model fidelity
- Free-tier rate limits and token caps make automated testing
  impractical
- The generation flow requires complex orchestration: dependency
  resolution, prompt assembly, retry logic, output validation

In contrast, local agents (Claude Code, Cursor, Codex CLI) work
well because they read template files directly from disk — no
prompt assembly or token limits apply.

## Decision

The product is the **composable template library**, not a
generation tool. Generation is a user-space concern.

1. **Templates are the product** — the deliverable is a
   well-structured, composable set of Markdown templates with
   machine-readable metadata (manifest.yaml)
2. **Generation is not guaranteed** — we document the available
   paths (local agent, web portal, API) and their trade-offs,
   but do not own or guarantee the generation step
3. **Local agent is the recommended path** — attach the interview
   template and the relevant stack to a local agent; it reads
   files directly and produces the best results
4. **E2e tests validate templates, not generation** — tests
   confirm that templates are structurally correct and that
   prompts are well-formed, not that any particular model
   produces perfect output

## Alternatives considered

- **Build a generation CLI** — rejected; duplicates what local
  agents already do well, adds maintenance burden, and ties the
  project to a specific model provider
- **Optimize prompts for API generation** — rejected; prompt
  engineering is fragile across model versions and does not
  solve the fundamental token-limit problem for large stacks

## Consequences

- The resolve.py script (#236) focuses on dependency resolution
  and prompt assembly for testing, not as a user-facing tool
- User paths documentation (#237) describes trade-offs honestly
  rather than promising reliable generation
- E2e test scope narrows to structural validation and lightweight
  canary checks
- Contributors do not need API keys to validate their changes

## References

- PR #235 — provider-agnostic SDK migration and e2e findings
- Issue #100 — original e2e runner task
- Issue #236 — resolve.py script
- Issue #237 — document user paths
