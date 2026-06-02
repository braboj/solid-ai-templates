---
id: 008
status: Accepted
date: 2026-05-06
category: process
supersedes: []
superseded_by: []
---

# ADR-008: Issue and PR naming conventions

## Context

There was no documented convention for issue titles or PR titles.
Some PRs included ticket numbers, others did not. Squash-merge
commit messages derive from PR titles, so inconsistency in titles
creates inconsistency in the git log.

## Decision

### Issue titles

- Sentence case, imperative verb: "Add X", "Fix Y", "Remove Z"
- No type prefix — the issue label carries the type
- No ticket number — it is assigned by GitHub

### PR titles

- Conventional Commits format: `<type>(<scope>): <summary>`
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`
- Include the issue number(s) at the end: `(#123)` or `(#123, #456)`
- Summary in lowercase, imperative, under 70 characters
- Examples:
  - `feat(stack): add python-celery-worker template (#180)`
  - `fix: correct dependency chains across stacks (#271, #274)`
  - `docs: add terminology review checklist (#285)`

### Squash-merge commit messages

- PR title becomes the commit subject line (automatic with squash)
- PR body becomes the commit body (automatic with squash)
- No manual editing of the squash commit message needed

## Alternatives considered

1. **No convention** — status quo; leads to inconsistent git log
2. **Conventional Commits for issues too** — adds noise; issue
   titles are read by non-developers; labels serve the same purpose
3. **No ticket number in PR title** — loses traceability in
   `git log --oneline`; the number is the cheapest link back to
   the discussion

## Consequences

- Git log reads cleanly: every line has type, scope, summary,
  and ticket reference
- Issue titles remain human-readable without prefix noise
- No CI enforcement needed — this is a guideline, not a gate
