---
id: "016"
status: Accepted
date: 2026-06-26
category: process
supersedes: []
superseded_by: []
---

# ADR-016: Examples are agent-generated reference outputs

## Context

The files in `examples/*/CLAUDE.md` were written by hand. They have
drifted from the templates they claim to demonstrate: seven of eight
use a pre-`agents.md` free-form heading set (`## Project identity`,
`## Stack`, `## Commands`, ...) with no §5 Review process and no §6
Session protocol, while only one uses the current six-section output
shape. Two examples share a project name and demonstrate overlapping
stacks. Because examples are the reference outputs contributors
compare against, hand maintenance has repeatedly let them model an
outdated shape until someone audits them manually.

A deterministic resolved-chain reference already exists in
`generated/` (one file per stack, gated by `resolve.py --check`).
What `examples/` add on top of that is a *finished, named,
project-specific* context file — the end product a user would
actually commit. That value is real, but only if examples track the
output models instead of lagging them.

## Decision

Example context files are **outputs of the documented generation
path**, refreshed by re-running it — not artifacts edited by hand.

1. **Generated, not authored** — each `examples/*/CLAUDE.md` MUST be
   produced by attaching `templates/INTERVIEW.md`, the resolved stack
   chain (`generated/<stack>.md`), and the `agents.md` output models
   to a local agent. Example bodies MUST NOT be hand-patched to fix
   drift; regenerate instead.
2. **Inputs are recorded** — each example MUST state its generation
   inputs near the top: the stack source chain and a short project
   brief (name, owner, deployment, stack choices) sufficient to
   reseed regeneration.
3. **Conform to the output models** — every example MUST follow the
   `agents.md` six-section structure (§1 Project through §6 Session
   protocol, including a compliant §6.3 end-of-session audit).
4. **Regenerate on material template change** — when a template in
   an example's chain changes the output shape, that example MUST be
   regenerated, not selectively edited.
5. **Structure gated, coherence reviewed** — the smoke suite gates
   structure mechanically (every example declaring a session
   protocol is held to the §6.3 rule); semantic coherence and
   completeness are confirmed by review at regeneration time.
   Byte-for-byte reproduction is NOT expected — generation is
   non-deterministic.
6. **`generated/` stays authoritative** — the deterministic resolved
   chains in `generated/` remain the source-of-truth reference;
   `examples/` are illustrative finished outputs, not the canonical
   chain reference.

## Alternatives considered

- **Keep examples hand-maintained, add a heading-skeleton smoke
  gate** — rejected; hand maintenance is the source of the drift,
  and a structure gate alone does not keep section *bodies* honest
  to the templates.
- **Defer the whole refresh to the v3.0 restructure** — rejected;
  the examples already model an outdated shape and a two-format
  split, misleading contributors until then. The six-section
  skeleton is stable across the inline-to-reference change, so
  regenerating now is not wasted work.
- **Retire `examples/` and rely on `generated/` alone** — rejected;
  resolved chains show the composed template text, not a finished,
  named project file, which is the artifact users actually produce.
- **Build a generation CLI/tool to own the regeneration** —
  rejected; out of scope per existing project policy. The
  documented local-agent path is the maintenance method.

## Consequences

- #581 regenerates all eight examples through the pipeline, replacing
  the hand-written files, and verifies each is coherent and complete.
- The two same-named Go examples (`go-service`, chi router; and
  `metricshub`, Echo v4) demonstrate distinct stacks; regeneration
  disambiguates their project names.
- Regenerated examples adopt §6 Session protocol, so existing smoke
  coverage of the §6.3 rule widens automatically to more examples.
- `docs/PLAYBOOK.md` gains a "regenerate an example" procedure.
- The inline-versus-reference body style stays inline for now and is
  revisited when the restructure settles the recommended default.

## Related

- ADR-007 — establishes the local agent as the recommended
  generation path; this ADR adopts that path for maintaining the
  project's own examples.
- ADR-011 — provenance principle (outputs derived from real
  templates rather than theorized by hand).
