---
id: "035"
status: Accepted
date: 2026-09-01
category: composition
supersedes: []
superseded_by: []
---

# ADR-035: An orthogonal template is a resolution root, and its reach is measured there

## Context

A project resolves its stack, then the extras it opts into, then its
platform. Twenty of the manifest's entries are reachable only by the
second and third of those steps — the three platform templates, the six
optional backend modules, and eleven workflow, data and core extras. No
stack's `depends_on` names any of them.

The design record has said two different things about what that means.
The resolution algorithm resolves each opt-in entry the same way it
resolves a stack: its `depends_on` tree first, then itself. The system
specification said instead that the platform template and each extra are
appended as bare files, and that orthogonal templates are excluded from
reachability checks altogether.

The checks followed the specification. Every reachability check resolved
the seventeen stacks and stopped, so a file that reaches a reader only
through the opt-in path was scanned against zero chains. Nothing can be
missing from zero chains, so those files passed by arithmetic rather than
by inspection, and the suite reported a corpus it had never opened.

Four defects were live under that reading. Both platform templates
carried `[EXTEND: base-issues-types]`, whose parent section sits in a file
one stack chain of seventeen carries. Three templates — the agents, skills
and issue-format files — named a section of the quality-gates file in
running prose, which no chain of theirs carries. A project picking any of
them received a directive with no parent and a pointer to a section its
context file does not hold.

## Decision

1. **An orthogonal template is a root** — an entry no stack chain reaches
   MUST be resolved the way a stack is resolved: the core tier, then its
   `depends_on` tree, then itself. Appending the bare file is not
   resolution.

2. **Its guaranteed context is that chain and nothing more** — the stack a
   project pairs an orthogonal template with is unknown when the template
   is authored, so an `[EXTEND: ...]`, an `[OVERRIDE: ...]` or a prose
   section reference it carries MUST resolve within its own root's chain.
   A target that resolves only because some stack happens to supply it
   does not satisfy this.

3. **Reachability is checked over both corpora, counted separately** — the
   checks that resolve chains MUST resolve the stack roots and the opt-in
   roots, and MUST report each count. One corpus emptying while the other
   stays full is the failure this replaces, and a single total hides it.

## Alternatives considered

- **Leave the platform templates extending a section they cannot rely on,
  and document the risk** — rejected; the consequence lands on the
  consumer, who has no way to see that the parent is missing.

- **Have every stack depend on the issue-format file** — rejected; it buys
  the two platform templates their parent by adding a file to sixteen
  chains that do not want it, and leaves the other eighteen opt-in
  entries unchecked.

- **Check an orthogonal template against the union of every chain it could
  join** — rejected; a target present in one stack chain and absent from
  another would pass, which is the reading that hid the defect.

- **Give each orthogonal template a generated chain under `generated/`** —
  rejected for now; the checks resolve the chain in memory and need no
  artifact. Shipping thirty-seven pre-resolved files is a separate
  question about what a consumer downloads.

## Consequences

- `docs/SPEC.md` states the resolution of extras and the platform as
  dependency resolution rather than appending, and replaces the exclusion
  of orthogonal templates from reachability checks with the rule above.
- `TPL-06` and `SYS-11` resolve thirty-seven roots rather than seventeen,
  and report the stack and opt-in counts separately.
- `templates/platform/` joins the directories the smoke runner scans; it
  had been outside every file-level check.
- The three dangling prose references state their substance inline.
- An author adding an orthogonal template gets a smaller guaranteed
  context than a stack author does — six core files plus what the entry
  declares — and the checks now hold them to it.
