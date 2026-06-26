---
id: "017"
status: Accepted
date: 2026-06-26
category: templates
supersedes: []
superseded_by: []
---

# ADR-017: Stack templates follow a canonical section structure

## Context

The 30 stack templates grew independently and their section layout
drifted. An audit found the shape is mostly shared but inconsistent:
`Stack` (29/30), `Commands` (29/30), and `Project structure` (25/30)
are near-universal, but `python-service` — a usable stack — omits
`Commands`, the static-site stacks omit a `Testing` section, and the
language-conventions section is spelled five ways ("Code conventions",
"Coding conventions", "Crate conventions", "TypeScript conventions",
"Dart conventions").

Two existing structural facts shape what "required" can mean. Derived
stacks extend a parent (`python-fastapi` -> `python-service` ->
`python-lib`; `go-echo` -> `go-service` -> `go-lib`), so a section may
be satisfied by inheritance rather than repeated. And the core tier
(`base-quality, base-git, base-docs, base-readme, base-testing`)
resolves into every chain, so git/testing/quality/docs/readme rules
reach every stack regardless of the stack file.

Without a written structure and a gate, the drift recurs and stacks
cannot be compared like-for-like — which the upcoming stack-cleanup
work depends on.

## Decision

Stack templates follow a canonical section structure, classified with
RFC 2119 keywords. Membership is judged against the **resolved chain**,
not the raw file — a section a stack inherits from its parent counts as
present.

1. **MUST** — stack-unique sections that the core tier cannot supply;
   present in every usable stack's resolved chain:
   - `Stack`
   - `Commands`
   - `Project structure` — except pure-library stacks (e.g. `go-lib`,
     `rust-lib`), which prescribe no directory tree and MAY omit it.

2. **SHOULD** — present when the layer warrants; typically an
   `[EXTEND]` of a base/core section:
   - `Testing`, `<Language> conventions`, `Git conventions`,
     `Configuration`, `Quality gates`, `Error handling`.

3. **MAY** — domain-specific sections driven by the stack: routing,
   schemas, state management, components, styling, assets,
   accessibility, API integration, messaging, feature flags,
   authentication, observability, ORM/migrations, middleware,
   interceptors, concurrency, SEO, navigation, content structure,
   server setup/shutdown, and similar.

4. **Canonical order** — sections appear in this order when present:
   `Stack` -> `Project structure` -> language and domain sections ->
   `Testing` -> `Git conventions` -> `Commands`. `Commands` is last.

5. **Language section name** — the language-conventions section MUST be
   named `<Language> conventions` (e.g. `Python conventions`,
   `Go conventions`, `TypeScript conventions`, `Rust conventions`,
   `Dart conventions`). It maps to output section 2.2 `[Language]`.
   `Code conventions` is reserved for genuinely language-agnostic code
   rules.

6. **Inheritance** — a derived stack MUST NOT repeat a section it
   inherits unchanged; it adds, `[EXTEND]`s, or `[OVERRIDE]`s. Every
   MUST section MUST still be reachable in the resolved chain.

7. **Enforcement** — the MUST tier is gated by smoke check `SYS-06`
   (spec `SAIT-SMK-SYS-06-001A`): for every usable stack, the resolved
   chain contains `Stack`, `Commands`, and `Project structure` (with
   the library exception). The SHOULD/MAY tiers stay declarative.

## Alternatives considered

- **Leave structure to convention** — rejected; unwritten convention
  is exactly what drifted across 30 files.
- **Require an identical fixed section list in every file** — rejected;
  it would force irrelevant sections (e.g. `Routing` in a library) and
  fights the inheritance model.
- **Gate on the raw file rather than the resolved chain** — rejected;
  it would force derived stacks to repeat inherited sections, defeating
  composition.
- **Standardize on `Code conventions`** — rejected; `<Language>
  conventions` is the plurality, is more informative, and maps to the
  output `[Language]` subsection.

## Consequences

- #640 fixes the current drift: add `Commands` to `python-service`,
  add a `Testing` section to the three static-site stacks, and rename
  the outlier language sections to `<Language> conventions`.
- #641 implements `SYS-06` and registers the spec in `tests/`.
- New stack templates must follow this structure; the authoring steps
  in CLAUDE.md and PLAYBOOK reference it.
- `generated/` chains for the edited stacks are regenerated.

## Related

- ADR-001 — the inheritance/composition model this structure builds on.
