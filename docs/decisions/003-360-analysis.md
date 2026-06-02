---
id: "003"
status: Accepted
date: 2026-04-28
category: process
supersedes: []
superseded_by: []
---

# ADR-003: 360-degree analysis as a reusable template

## Context

Existing review templates (base/review.md for code review,
base/scope.md for session audit) are purely technical. They miss
user value, business viability, and marketing discoverability.
A 360-degree analysis was performed ad-hoc on tutorial-git and
proved useful, but the methodology was improvised and all four
perspectives were evaluated from a developer lens.

## Decision

Add base/360.md as a four-category assessment template:

1. **Value** (user) — functional completeness, content quality,
   usability, trust, accessibility, performance
2. **Quality** (engineer) — architecture, code, testing, CI/CD,
   security, documentation
3. **Viability** (analyst) — licensing, cost, maintainability,
   dependency and operational risk
4. **Discovery** (marketer) — positioning, SEO effectiveness,
   social shareability, analytics, distribution

Each category has a role prompt that the evaluating agent MUST
adopt. Categories are independent and SHOULD be executed as
parallel subagents — each starts with a clean context to enforce
structural perspective isolation (not just instructional).

The Value agent reads user-facing materials (README capability
list, landing page, docs/user-journeys.md) and verifies promises.
It does NOT read developer documentation.

## Alternatives considered

1. **Extend base/review.md with non-technical checks** — rejected:
   review.md is scoped to PR changes, not whole-project assessment.
2. **Single-agent sequential evaluation** — rejected: perspective
   bleed causes all four categories to collapse into a developer
   review. Parallel subagents with clean contexts fix this.
3. **Separate templates per category** — rejected: the four
   categories are designed to be used together; splitting them
   loses the summary table and overall grade.

## Consequences

- Projects can run a structured assessment before launch, at
  milestones, or quarterly
- The Value agent needs a README with a capability list
  (base/readme.md updated to require this)
- Cross-feature user journeys should be documented in
  docs/user-journeys.md for the Value agent to verify
- The overall grade is the lowest category grade — the project
  is only as strong as its weakest perspective
