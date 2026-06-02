---
id: 010
status: Accepted
date: 2026-06-02
category: process
supersedes: []
superseded_by: []
---

# ADR-010: ADR governance model

## Context

The `docs/decisions/` folder holds 9 ADRs and will grow as the
project accumulates structural decisions. The current state has
five gaps that compound as the folder grows:

- **Inconsistent headers** — ADRs 001-005 and 008 use the
  `# ADR-NNN: title` form with inline `**Status:** Accepted` /
  `**Date:** YYYY-MM-DD`; ADRs 006, 007, and 009 use
  `# ADR NNN — title` with `## Status` blocks. None carry
  machine-readable metadata, so smoke checks cannot enforce
  invariants and tooling cannot filter or sort ADRs without
  parsing prose
- **No backward links** — when a new ADR supersedes an old one,
  the old ADR is not updated to point forward. A reader landing
  on the old ADR via a stale link has no signal it is outdated.
  ADR-004 already supersedes ADR-001's depend-on-transitive-IDs
  rule, but ADR-001 carries no `superseded_by` reference
- **No archival convention** — superseded ADRs sit alongside
  current ones in the same flat directory. At 50+ ADRs, the
  directory becomes hard to scan
- **No self-sufficiency rule** — nothing prevents new ADRs from
  saying "see ADR-X for the rationale," which is fine at write
  time but rots when ADR-X is later superseded
- **No categorization** — there is no way to filter ADRs by area
  (composition, tooling, process, release) without reading each
  one

This ADR proposes a single governance model covering frontmatter,
two-way links, archival, self-sufficiency, and categorization.
Implementation (migration of ADRs 001-009, smoke check, CLAUDE.md
update) is tracked as follow-up tasks.

## Decision

### 1. YAML frontmatter on every ADR

Every ADR (new and migrated) starts with a YAML frontmatter block
carrying the machine-readable metadata:

```yaml
---
id: NNN                       # zero-padded sequence: 010, 011, ...
status: Accepted              # one of: Proposed, Accepted, Superseded
date: YYYY-MM-DD              # date the status was last changed
category: process             # see closed set below
supersedes: []                # list of IDs this ADR supersedes
superseded_by: []             # list of IDs that supersede this one
---
```

Frontmatter rules:

- `id` MUST match the filename's leading digits
- `status` MUST be one of the three values; no other values allowed
- `date` MUST be present and MUST update whenever `status` changes
- `category` MUST be one of the closed set (see below)
- `supersedes` and `superseded_by` MUST be present even when empty
- Frontmatter is the source of truth for status/date/links — prose
  `## Status` sections are removed during migration to avoid drift

Rejected alternative: prose headers plus a separate index file. The
index would duplicate data and need re-sync on every change. YAML
frontmatter keeps metadata next to the prose and parses cleanly
without extra tooling.

### 2. Closed category set

```
composition   — inheritance, EXTEND/OVERRIDE, dependency graph,
                manifest shape
templates     — template authoring conventions, ID system, layer
                organization, naming
tooling       — sync.py, resolve.py, tests/, smoke-check shape
process       — issue/PR conventions, labels, milestones, session
                protocol, release process, this ADR
release       — versioning scheme, tag format, release notes,
                version manifest
```

New categories require a new ADR. The closed set forces explicit
scope-of-impact thinking.

### 3. Two-way links via the `superseded_by` field

When a new ADR supersedes an old one, the merging PR MUST update
the old ADR's `superseded_by` field to include the new ADR's id
and update the old ADR's `status` to `Superseded` and `date` to
the merge date.

This is the ONE exception to the existing immutability rule —
metadata fields tracking supersession may be updated on a
previously-merged ADR. The prose body (Context, Decision,
Alternatives, Consequences) remains immutable.

Enforcement is a smoke check (see follow-up tasks). For now, the
convention is enforced by review: PRs that supersede an existing
ADR MUST update the old ADR's frontmatter in the same PR.

### 4. Archival via status filter, not directory move

Superseded ADRs stay in `docs/decisions/`. Filtering by
`status: Superseded` answers "what's archived" without breaking
deep links, git blame continuity, or the `NNN-slug.md` ordering.

A future index page (generated, not hand-maintained) can present
the active set separately from the archived set.

Rejected alternative: move superseded ADRs to
`docs/decisions/archive/`. The break in deep links and the loss of
contiguous numbering outweigh the visual benefit.

### 5. Self-sufficiency: ADRs do not cite other ADRs in prose

The existing rule in `base/core/docs.md` says ADRs MUST NOT
reference future ADRs. This ADR extends it: ADRs MUST NOT cite
other ADRs in their prose body except via the frontmatter
`supersedes` and `superseded_by` links.

A "## Related" section MAY appear at the end for context-only
pointers, but MUST NOT carry decision-bearing text — moving a
related ADR or superseding it MUST NOT change the meaning of this
ADR's Decision section.

Rationale: prose references rot. The frontmatter graph is the only
ADR-to-ADR link that smoke checks can validate, so prose links
have no enforcement and silently drift.

### 6. Title and filename conventions

- Filename: `NNN-kebab-case-slug.md` (existing convention, no change)
- H1 title: `# ADR-NNN: Title in sentence case` — colon form, not
  the em-dash form used by ADRs 006, 007, 009. Sentence case
  matches the rest of the project's heading style

### 7. Migration plan (separate PR)

ADRs 001-009 are migrated in a single follow-up PR. The migration:

- Adds frontmatter to each file using the existing metadata
  (status, date) extracted from prose
- Removes the redundant prose `## Status` and `**Status:**` /
  `**Date:**` lines
- Renames H1 titles to the colon form where needed
- Sets `category` based on each ADR's subject matter
- Populates `supersedes` and `superseded_by` for the ADR-001 ↔
  ADR-004 supersession (and any other reciprocal links discovered
  during migration)
- Resolves ADR-009's stale `Proposed` status (set to `Accepted`,
  date 2026-05-31 to match v2.5 release where the cap was applied)

The migration is a single mechanical PR — it does NOT rewrite the
prose body of any ADR. Immutability is preserved.

## Alternatives considered

- **Prose headers + index file** — rejected; duplicates metadata
  and needs re-sync. YAML frontmatter co-locates the data with
  the prose
- **Move superseded ADRs to `archive/`** — rejected; breaks deep
  links and git blame continuity. Status filtering achieves the
  same scan-by-active benefit without those costs
- **Allow prose ADR-to-ADR references with link checking** —
  rejected; link checking confirms the file exists but cannot
  detect that the *meaning* drifted when the target ADR was
  superseded. Only frontmatter links carry enforceable semantics
- **Free-form categories** — rejected; without a closed set,
  category becomes meaningless within months as new ADRs invent
  new buckets
- **Mutable ADRs** — rejected; explicitly out of scope per the
  issue. Immutability is preserved; only frontmatter links change

## Consequences

- All new ADRs MUST follow this schema, starting with this ADR
- `templates/base/core/docs.md` ADR rules are updated in a
  follow-up PR to point to the schema (the ADR is the source of
  truth; docs.md summarizes)
- ADRs 001-009 are migrated in one follow-up PR (mechanical, no
  prose rewrites)
- A smoke check is added in a follow-up PR enforcing: frontmatter
  present and well-formed, `id` matches filename, `status` in
  closed set, `category` in closed set, reciprocal
  `supersedes`/`superseded_by` consistency
- A `docs/decisions/TEMPLATE.md` lands with this PR as the
  canonical example new ADR authors copy from
- `CLAUDE.md` §2.9 is updated in a follow-up PR to summarize this
  schema and point to TEMPLATE.md
- ADRs become filterable, sortable, and validatable without prose
  parsing; the folder scales beyond 50 entries without becoming
  hard to scan

## Related

- The pattern of co-locating empirical observations next to data
  (ADR-style governance for a different artifact type) is the
  Findings docs convention added to `base/core/docs.md` for
  empirical-threshold tracking
- The immutability rule this ADR extends lives in
  `base/core/docs.md` under `## Decision logs`
