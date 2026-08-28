---
id: "027"
status: Accepted
date: 2026-08-28
category: composition
supersedes: []
superseded_by: []
---

# ADR-027: The language layer owns per-language tool selection

## Context

The gate model distinguishes a category that MUST be enforced from the
concrete tool that enforces it, and states that stack templates perform
the mapping. In practice the mapping had no consistent home and settled
in three different places.

The abstract gate file names concrete tools directly: `complexipy` for
Python and `eslint-plugin-sonarjs` for TypeScript, in the complexity
section and in a recommended-plugins list. Some stack files name their
own — the Python library stack names `pre-commit`, `ruff`, `mypy` and
`pyproject.toml`; the Astro stack names `husky` and `lint-staged`. The
`base/language/` layer, which exists for language bindings, held only
`typescript.md`, and that file carried style rules with no tooling
section at all. There was no `python.md`.

Two costs follow. The abstract policy layer depends on concrete details,
so it changes when a tool is replaced as well as when the policy moves.
And six Python stacks resolve through one root stack file, so a tool
named there is either repeated per stack or absent from the stacks that
do not inherit it.

## Decision

1. **The language layer is the home** — per-language tool selection MUST
   live in `templates/base/language/<language>.md`, in a section tagged
   `[ID: base-<language>-tooling]` that binds a concrete tool to each
   category the gate model declares.

2. **The abstract gate names no tool** — `base-quality-gates` MUST state
   categories, layers, thresholds and ratchet mechanics only. Where a
   category has no binding without a specific tool, the gate states the
   requirement and the language file names the tool.

3. **Stacks bind only what their shape changes** — a stack template MUST
   NOT re-declare a tool its language file already binds. It adds the
   tools its own shape introduces, such as a library's build and publish
   step, and tools that are not language-specific, such as secret
   detection.

4. **A language file is reached through the root stack of its family** —
   the language file is declared as a dependency of the stack that other
   stacks in that family already resolve through, so one declaration
   reaches the family.

## Alternatives considered

- **Leave tool names in the abstract gate** — rejected; the policy file
  then has two independent reasons to change, and adding a language
  means editing the abstraction.
- **Put every tool in each stack file** — rejected; six Python stacks
  would repeat one table, and a tool replacement becomes a six-file edit
  whose legs can drift apart.
- **A single cross-language tool-mapping file** — rejected; it groups by
  the wrong axis. Reading it requires filtering out every ecosystem the
  project does not use, and it would resolve into chains for languages
  the project does not have.
- **Bind tools in the platform layer** — rejected; platform templates are
  chosen per project and orthogonal to the stack, so a Python tool bound
  there would be absent whenever another platform is picked.

## Consequences

- `templates/base/language/python.md` is created and registered, and
  `typescript.md` gains a tooling section.
- `stack-python-lib` declares `base-python`, which reaches the six Python
  stacks that resolve through it.
- The Python library stack drops the tool rows the language layer now
  owns and keeps its docstring, secret-detection and build rows.
- The concrete complexity tools leave `base-quality-gates`, which changes
  what that file's complexity section and recommended-plugins list say.
- Adding a language means adding one file and one dependency edge, with
  no change to the abstract gate.
