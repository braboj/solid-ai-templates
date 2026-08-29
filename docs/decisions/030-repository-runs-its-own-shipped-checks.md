---
id: "030"
status: Accepted
date: 2026-08-29
category: tooling
supersedes: []
superseded_by: []
---

# ADR-030: This repository runs the checks its templates ship

## Context

The templates embed runnable checks — a command plus a pass condition,
placed beside the rule each verifies. There are 44 of them across 13
files.

Nothing ran them here. `run_smoke.py` checks that the templates
*compose*: that `[DEPENDS ON]` resolves, that IDs are unique, that chains
are non-empty, that a prose reference resolves per chain. It says nothing
about whether this repository obeys the rules it publishes, and this
repository is a consumer of its own base tier.

Three rules shipped and were violated here, each found by hand, each
after the rule had already merged: the community-health files, the
comment layout in 29 places, and the changelog. In two of the three the
violation was found in the same session that shipped the rule, which is
luck rather than process.

A rule its own author's repository violates is weak evidence for the
rule. Either the rule is wrong or the repository is, and until something
runs the check nobody knows which.

The obvious implementation does not work. The embedded checks are written
for a consuming project and several do not apply here — a `scripts/`
directory this repository does not have, a wheel it does not build, an
SBOM it has no dependencies to describe. A runner that fails on those is
noise. One that skips them silently reproduces the original problem,
because an empty result and an unreached check look identical.

## Decision

1. **The checks run here** — `tests/run_conformance.py` extracts every
   runnable fenced block under `templates/` and runs it against this
   repository, in CI, on every pull request.

2. **Every runnable block MUST carry a disposition** in
   `tests/conformance.py`: run it, or skip it with the reason it does not
   apply. A block with no entry FAILS the run. This is what stops a check
   added to a template from arriving unexamined, and it makes "does not
   apply" a written claim rather than an absence.

3. **Extraction is reconciled against a wider count** — the runner parses
   fenced blocks in every language and reports the runnable subset against
   that total. An extraction that silently under-counts is
   indistinguishable from a clean one, and reporting its own tally does
   not catch it.

4. **A block is located by a string only its body contains**, never by
   position. `base/core/git.md` alone holds ten.

5. **Extracted checks run from a directory outside the tree they
   inspect**, so a check cannot match its own extracted source.

6. **A run that executes nothing fails.** Every check reported as not
   applicable is a check that verified nothing, so an all-skip run is a
   failure rather than a pass.

## Alternatives considered

- **Add them to `run_smoke.py`** — rejected; smoke answers a different
  question, and mixing composition checks with conformance checks makes a
  failure ambiguous about which kind broke.
- **Skip inapplicable checks silently** — rejected; it reproduces the
  defect the checks themselves warn about. The reason a check does not
  apply is the part worth keeping, because it is what a later reader
  re-derives otherwise.
- **Baseline the current violations and ratchet** — rejected; this
  repository rejects a freeze table with no suppression beside it, and the
  known gaps were small enough to fix instead.
- **Run them by hand at the wrap-up audit** — rejected; that is what was
  already happening, and it is how three violations reached `main`.

## Consequences

- Adding a fenced `bash` or `python` block to a template now obliges the
  author to add its disposition. `CLAUDE.md` section 6.2 carries the rule.
- 19 checks run against this tree; 25 are recorded as not applying, each
  with its reason.
- CI needs full history, because checks reading the tag list fail on a
  shallow clone, and a token for the checks that reach GitHub.
- The runner found a defect on its first pass: the bare-suppression check
  in `base-quality-gates` had no exclusion list and walked `.venv`,
  reporting 467 suppressions across 3586 files where the project's own
  count is 1 across 10.
- A pass condition that cannot be expressed mechanically is recorded as
  such and reported for an operator to read, rather than being given a
  brittle assertion.
