---
id: "047"
status: Accepted
date: 2026-09-26
category: templates
supersedes: []
superseded_by: []
---

# ADR-047: Guide docs under docs are kebab-case, and the playbook keeps its name

## Context

`templates/base/core/docs.md` resolves into every chain, and its standard
documents table names `docs/ONBOARDING.md`, `docs/PLAYBOOK.md` and
`docs/SPEC.md`. A note under the table fixes a casing split: single-word
guide docs are SHOUT-case, multi-word ones lower kebab-case
(`docs/dev-journal.md`). Every generated project inherits those filenames.

Two objections were raised against the names. The first is the casing: two
consuming projects reported the SHOUT-case files under `docs/` as
distracting, and one of them is already renaming its guide docs to
kebab-case as a local departure. The second is the noun: `playbook` was
questioned against `runbook`, because the table describes the file as an
"operational reference" and the tracker calls its release section "the
release runbook".

The two had to be decided together. Either one alone renames a MUST
document in every consuming project, and answering them apart would rename
the same file twice. At the time of the decision, 13 consuming repositories
carried `docs/PLAYBOOK.md`, and 12 of them `docs/ONBOARDING.md`.

## Decision

1. **Every file under `docs/` uses lower kebab-case** — the standard
   documents become `docs/onboarding.md`, `docs/playbook.md` and
   `docs/spec.md`, beside `docs/dev-journal.md`. The single-word/multi-word
   split is withdrawn.
2. **Root files keep the names their ecosystem fixes** — `README.md`,
   `CLAUDE.md`, `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`,
   `SECURITY.md`, `CODE_OF_CONDUCT.md` and `LICENSE` are named by GitHub or
   by the agents that read them, and stay upper case. The rule is read from
   the path: in the root, the ecosystem's name; under `docs/`, kebab-case.
3. **The playbook keeps its noun** — the file holds recipes for tasks a
   contributor chooses to perform. Its purpose in the standard documents
   table changes from "Operational reference for common tasks" to "Recipes
   for recurring contributor tasks". A release procedure inside it MAY be
   called a runbook without renaming the file.
4. **The rule takes effect in the v3.0 release** — a renamed MUST document
   is a breaking change, and v3.0 is the release that carries breaking
   changes. Until that release, the current split governs.
5. **Existing projects rename when they adopt v3.0** — a project MUST NOT
   be renamed ahead of its move to v3.0, and a project that moves MUST
   rename all three files in the same change. Newly generated projects use
   the new names from v3.0 on.

## Alternatives considered

- **Keep the split** — rejected; two consumers reported friction, and a
  rule that depends on how many words a filename holds is one a reader
  cannot apply without the table.
- **Rename `playbook` to `runbook`** — rejected; a runbook answers a running
  system that misbehaves. One section of the playbook is shaped that way,
  and the rest are authoring recipes.
- **Kebab-case for every file, the root included** — rejected; GitHub finds
  community health files and agents find their context files by those
  exact names.
- **Rename every consumer at once** — rejected; it costs about 13 pull
  requests of hand edits outside the release that makes the change. A
  consumer not yet on v3.0 would then carry names its templates do not
  state.
- **New projects only, existing ones never renamed** — rejected; it splits
  the estate for good, and every consumer's `docs.md` would disagree with
  its own tree from its first upgrade on.

## Consequences

- At v3.0, `templates/base/core/docs.md` renames the three rows, rewrites
  the playbook's purpose, replaces the casing note with the path rule, and
  updates every other template naming the three files
- This repository renames its own three guide docs in the same release, and
  `py tools/sync.py` regenerates the chains
- The v3.0 migration guide for consuming projects carries the rename: the
  three `git mv` commands and the reference rewrite, run on each project's
  move to v3.0
- The CHANGELOG entry for v3.0 names the rename as a breaking change
- A consumer already on kebab-case needs no local departure from v3.0 on
