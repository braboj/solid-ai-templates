---
id: "028"
status: Accepted
date: 2026-08-28
category: composition
supersedes: []
superseded_by: []
---

# ADR-028: A prose reference to another template's section is bounded by chain reach

## Context

Templates cross-reference each other in two distinct ways. Structural
directives — `[DEPENDS ON: ...]`, `[EXTEND: ...]`, `[OVERRIDE: ...]` —
are resolved by the composition tooling and checked by the smoke suite,
which fails a directive naming a section that is not reachable in the
resolved chain.

Running prose does the same thing with no mechanism behind it. A rule
that reads "`base-quality-gates` states which categories a project MUST
gate; this table names the tool that satisfies each" is a reference in
every sense that matters to a reader, and in none that the tooling sees.

The two files sit at different depths in the dependency graph, so such a
reference is not uniformly true or false. It resolves in the chains that
carry both files and dangles in the rest. A consumer whose context file
contains the referencing rule but not the referenced section is sent to
something their file does not have, with nothing anywhere reporting it.

Measured across the tree on 2026-08-28: 15 cross-file prose references,
of which 3 dangled in at least one chain. `core/git.md` resolves into all
17 chains and `core/examples.md` into 11, so a reference between them is
unreadable in six. One reference named a section declared in a template
that resolves into no chain at all, making it unreadable in all 17 — and
it had been introduced knowingly weeks after two others were removed for
exactly this reason, which is the evidence that the constraint was
understood and not written down.

## Decision

1. **Prose reference** — a template MUST NOT name another template's
   section ID in running prose unless the file declaring that section
   resolves into every chain that carries the referencing file.

2. **Default remedy** — where that condition does not hold, the rule MUST
   state its substance inline. Naming the concept rather than the section
   ID keeps the sentence true in every chain, since a chain lacking the
   rule also lacks the sentence's premise.

3. **Scope** — this governs prose only. Structural directives are
   unaffected; their reachability is already resolved and already
   checked.

4. **Enforcement** — the constraint MUST be checked per chain rather than
   per file, because a reference is well-formed in both files and defective
   only in the chains that carry one and not the other. The check MUST
   report the number of chains it resolved and the number of references it
   matched, since a check that reaches nothing and a clean tree otherwise
   produce the same empty result.

## Alternatives considered

- **Add the declaring file to every chain that carries the referencing
  one** — rejected; it inflates chains to satisfy a sentence, and the
  files that most attract references are the ones deliberately scoped to a
  subset. One referenced file resolves into no chain by design.
- **Forbid cross-file section references entirely** — rejected; a
  reference between two files that genuinely co-occur in every chain is
  correct and useful, and a blanket ban would remove working sentences to
  prevent a defect that measurement bounds at three.
- **Check without stating a rule** — rejected; a failure with no rule
  behind it reads as tooling noise, and the fix an author reaches for is
  whatever silences it, which here is adding a dependency.
- **State the rule without a check** — rejected; the defect is invisible
  from either file, so review cannot catch it. The instance that prompted
  this was introduced by an author who had removed two of the same kind
  hours earlier.

## Consequences

- `docs/SPEC.md` gains the constraint under the section tag grammar,
  where an author reads the reference syntax.
- `CLAUDE.md` carries a one-line authoring rule pointing at it.
- Smoke check SYS-11 resolves every chain and fails on any prose
  reference absent from one carrying its referencing file, on a
  reference naming an ID no template declares, and on its own inputs
  being empty.
- Three existing references were restated inline rather than repaired by
  dependency: two in `base/core`, one in the TypeScript language file.
- Authors gain a constraint that is cheap to satisfy and expensive to
  detect by eye, which is the shape that justifies a check rather than a
  convention.
