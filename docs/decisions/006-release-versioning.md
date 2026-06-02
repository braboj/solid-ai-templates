---
id: 006
status: Accepted
date: 2026-05-04
category: release
supersedes: []
superseded_by: []
---

# ADR-006: Release versioning and process

## Context

The release template (`base/infra/release.md`) prescribed a four-digit
versioning scheme (`MAJOR.MINOR.BUILD.PATCH`). This is non-standard —
the industry default is three-digit SemVer (`MAJOR.MINOR.PATCH`). The
BUILD segment added complexity without solving a clear problem for most
projects.

The release process in `base/core/git.md` assumed every project has a
version manifest to bump (`package.json`, `pyproject.toml`, etc.). For
no-build projects (plain Markdown, documentation, templates), this
created an awkward step with nothing to change.

## Decision

1. **Three-digit SemVer** — adopt standard `MAJOR.MINOR.PATCH` in
   `release.md`, dropping the BUILD segment
2. **Milestones map to minor bumps** — each milestone closes with a
   minor version release (e.g. v2.1, v2.2)
3. **No-build release variant** — projects without a version manifest
   tag main directly and create a GitHub Release with auto-generated
   notes, skipping the chore PR
4. **Build projects keep the chore PR** — projects with a manifest
   still follow the branch → bump → PR → merge → tag flow

## Alternatives considered

- **Keep four digits** — rejected; non-standard, confusing for
  contributors, no tooling support
- **CHANGELOG.md for no-build** — rejected; GitHub Releases
  auto-generate notes from merged PRs, avoiding manual maintenance
- **Empty commits** — rejected; some CI rejects them, and they add
  noise to history

## Consequences

- `release.md` versioning section updated to three-digit SemVer
- `git.md` release process updated with a no-build variant
- Existing tags (v2.0.0, v2.1.0) already follow three-digit SemVer
