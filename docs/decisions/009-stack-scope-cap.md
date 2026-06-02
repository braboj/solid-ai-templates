---
id: "009"
status: Accepted
date: 2026-05-31
category: templates
supersedes: []
superseded_by: []
---

# ADR-009: Stack scope cap

## Context

The template library currently contains 30 stack templates covering
Python, Go, Java, Node, Rust, mobile, SSG, SPA, full-stack, and IaC.
Every new framework or variant is a candidate for a new stack
template, which creates a growth trajectory toward hundreds of files.

This growth is harmful:

- **Maintenance burden** — each stack must stay in sync with base
  template changes; 100 stacks means 100 files to validate on every
  base change
- **Quality dilution** — niche stacks receive less review and drift
  faster than popular ones
- **Opinionation creep** — the more stacks we add, the more
  framework-specific opinions we encode, moving away from the
  project's role as a composable foundation
- **Wrong layer** — teams and companies have internal frameworks,
  conventions, and tooling that stack templates cannot anticipate;
  they should own their stacks

The real value is in the base and layer templates (quality, git,
testing, security, OWASP, 12-factor, CI/CD) — these codify universal
standards that do not change per team. Stack templates are reference
implementations demonstrating how to compose the base.

Current usage confirms this: across all templates, there are 141
`[EXTEND:]` directives and only 22 `[OVERRIDE:]` directives. All
overrides are stack-on-stack (e.g. fastapi overrides python-lib).
Base templates are almost never overridden — only extended. This
means the composition model already supports downstream extension
with minimal friction.

## Decision

1. **Cap the stack library** — solid-ai-templates maintains a
   curated set of stacks covering major framework categories, not
   every variant. The current ~30 stacks are sufficient.
2. **New stacks require justification** — a new stack is accepted
   only if it represents an uncovered category (e.g. a new language
   ecosystem), not a variant of an existing one.
3. **Prioritize base quality over stack breadth** — effort goes
   into strengthening base, security, workflow, and data templates
   rather than adding stacks.
4. **Company/team stacks live elsewhere** — organizations that need
   custom stacks (internal frameworks, company conventions, extended
   rules) maintain them in their own repository. Imbra's own
   extended stacks live in a separate `imbra-ltd/imbra-stacks`
   repository (or equivalent).
5. **Public community stacks** — if community demand grows, a
   separate `solid-ai-templates-community` repository can host
   contributed stacks with lighter review standards. The core repo
   does not merge community stacks.

## Fork-and-extend workflow

The intended consumption model for teams and companies:

```
solid-ai-templates (upstream)        your-org/your-templates (fork)
├── templates/base/        ───fork──► ├── templates/base/          (inherited)
├── templates/backend/     ───fork──► ├── templates/backend/       (inherited)
├── templates/frontend/    ───fork──► ├── templates/frontend/      (inherited)
├── templates/stack/       ───fork──► ├── templates/stack/         (reference only)
│                                     ├── templates/stack/         (add your own)
│                                     ├── templates/company/       (new layer)
│                                     │   ├── jira.md              (issue tracking)
│                                     │   ├── confluence.md        (documentation)
│                                     │   └── conventions.md       (team rules)
│                                     └── templates/manifest.yaml  (extended)
```

### Steps

1. **Fork** solid-ai-templates into your organization
2. **Add stacks** — create stack templates under `templates/stack/`
   using `[EXTEND:]` to build on base and layer templates
3. **Add company conventions** — create new templates for
   org-specific concerns (issue tracking, document storage, team
   workflow) as new `[ID:]` sections — no override needed
4. **Override sparingly** — use `[OVERRIDE:]` only when a base rule
   genuinely does not apply (e.g. embedded C cannot follow standard
   testing conventions)
5. **Track upstream** — periodically pull from upstream to pick up
   base template improvements:
   ```bash
   git remote add upstream https://github.com/braboj/solid-ai-templates.git
   git fetch upstream
   git merge upstream/main
   ```
6. **Register in manifest** — add new templates to
   `templates/manifest.yaml` so smoke tests validate the full set

### Design principle

The composition model is designed so that downstream forks rarely
need `[OVERRIDE:]`. Company-specific concerns are additive — they
introduce new sections rather than replacing base rules. If a fork
finds itself overriding many base sections, that signals a problem
in the base templates (too opinionated) rather than a valid use case.

## Alternatives considered

- **Accept all stacks** — rejected; leads to maintenance burden
  and quality dilution as described above
- **Stack plugins via submodules** — rejected; adds complexity
  for users who just want to attach a file to their agent
- **Monorepo with tiers** (core vs community) — rejected; blurs
  the quality boundary and makes it unclear which stacks are
  maintained

## The hourglass model

```
        Many teams / orgs / developers
             (forks, submodules)
                     │
                     ▼
       ┌─────────────────────────┐
       │   solid-ai-templates    │  ← narrow waist
       │   (base + layers only)  │
       └─────────────────────────┘
                     │
                     ▼
          Many agents / tools
     (Claude Code, Cursor, Copilot,
      Codex CLI, Devin, Windsurf...)
```

The narrow waist is the set of universal, language-agnostic standards:
OWASP, 12-factor app, SOLID, testing, git, security, CI/CD. These
are stable, unopinionated, and rarely overridden.

Everything above the waist varies freely — each team adds their own
stacks, company conventions, issue tracking, and documentation
practices via `[EXTEND:]` and new `[ID:]` sections.

Everything below the waist varies freely — any agent that reads
Markdown can consume the templates. The output format adapts via
`templates/base/core/agents.md`.

This architecture maximizes reach: one curated set of base templates
serves any team on any agent, without the core repo growing
unbounded.

## Consequences

- PRs adding new stack templates are evaluated against the
  "uncovered category" criterion, not automatically accepted
- The README stacks table stays manageable (~30 rows)
- Teams fork or extend the base in their own repos — the
  composition model and manifest.yaml support this by design
- Imbra maintains its own extended stacks separately, eating
  its own dog food
- SPEC.md and CLAUDE.md are updated to document the scope cap
- PLAYBOOK.md documents the fork-and-extend workflow
