---
id: "018"
status: Accepted
date: 2026-06-26
category: process
supersedes: []
superseded_by: []
---

# ADR-018: docs/audits is the sole 360 audit-storage convention

## Context

The 360-degree audit template offered two ways to persist results: a
single-file history (`docs/360-audit.md`) holding one score row per
audit, or verbose dated reports under `docs/audits/YYYY-MM-DD-360.md`.
The template told authors to "pick one and never split across both,"
but stated no project-level choice — so the repository could (and did)
drift: history started in the single-file form, while sibling projects
used the dated-folder form.

Two forms with a per-project choice is an ambiguity, not a convention.
It invites split history, makes "where does the audit go?" a judgement
call on every run, and leaves nothing to mechanically verify. A single
prescribed location removes all three problems.

## Decision

1. **Single location** — Each 360 audit MUST be stored as a dated report
   at `docs/audits/YYYY-MM-DD-360.md`. This is the only audit location.
2. **No single-file history** — The single-file `docs/360-audit.md`
   form MUST NOT be used; all audit history lives in `docs/audits/`,
   one dated report per run.
3. **Mechanical enforcement** — A smoke check (`SYS-07`) MUST assert
   that no audit report exists outside `docs/audits/` and that every
   file there uses the dated `YYYY-MM-DD-360.md` name.

## Alternatives considered

- **Keep both forms with a per-project choice** — rejected; "pick one"
  still permits divergence between projects and leaves the location
  ambiguous on every run.
- **Single-file history only** — rejected; a bare score row ages poorly
  and loses the per-grade reasoning that makes an audit worth revisiting.
- **Dated folder, documented but unenforced** — rejected; a
  documentation-only rule drifts. Pair it with a mechanical check per
  the pair-the-check convention.

## Consequences

- `templates/base/workflow/360.md` [ID: 360-tracking] collapses to one
  convention and names its check; the `docs/PLAYBOOK.md` "Run a
  360-degree audit" section is aligned.
- The legacy `docs/360-audit.md` is migrated to
  `docs/audits/2026-05-04-360.md`; the single-file form no longer exists.
- A new smoke check `SYS-07` (spec `SAIT-SMK-SYS-07-001A`) guards the
  rule; the smoke suite grows by one check.
- Future audits append a new dated file under `docs/audits/`; no index
  or rollup history file is maintained.

## Related

- ADR-003 — introduced the 360-degree analysis as a reusable template.
- `templates/base/workflow/360.md` [ID: 360-tracking] — the audit
  tracking rule this ADR fixes.
- `SAIT-SMK-SYS-07-001A` — the paired mechanical check.
