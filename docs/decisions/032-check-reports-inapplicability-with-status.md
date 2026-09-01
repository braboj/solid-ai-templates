---
id: "032"
status: Accepted
date: 2026-09-01
category: tooling
supersedes: []
superseded_by: []
---

# ADR-032: A check reports run-time inapplicability with a reserved exit status

## Context

A check whose question is tied to a moment — a release being prepared, a
branch open for review, a migration under way — has empty inputs outside
that moment. The rule requiring such a check to detect the moment and
report that it does not apply, rather than emitting a count whose pass
condition assumes the moment is in progress, was adopted in v2.67.0 and
applied to the remaining checks in v2.68.0.

The runner had no result for that answer. A check reporting
inapplicability ran, printed a sentence, and exited clean, which the
runner recorded as a judgement awaiting a reading. Five of the twelve
readings a reader was asked to work through were checks that had already
answered, and the summary line overstated the outstanding work by the same
five.

Folding it into the existing skip disposition would lose that the check
ran and answered. A skip is decided in advance, by a person, about this
repository: this check cannot apply here at all. Inapplicability here is
decided at run time, by the check, about this moment, and the same check
applies next week.

Which membership moves. Measured on 2026-08-31 against a tree three
commits past a tag, two checks that had reported inapplicability the day
before were printing counts again, and one that had always reported it was
not in the set anyone had listed. A disposition recorded once cannot carry
a property that changes with the moment, so the signal has to come from
the check at run time.

## Decision

1. **Reserved status** — a check that determines at run time that it does
   not apply MUST report it with exit status 3, beside the sentence that
   explains it. The sentence is for whoever runs the block by hand; the
   status is what a runner reads.
2. **Not a phrase match** — a runner MUST NOT determine inapplicability by
   matching text in a check's output. A phrase is a convention no check
   declares, and rewording the sentence breaks the recognition silently.
3. **Counted apart** — a run's summary MUST count the checks that answered
   they do not apply separately from those awaiting a reading and from
   those a verdict was reached on.
4. **Distinct from a skip** — the status does not replace the disposition a
   person sets in advance. A skip records that a check cannot apply to this
   project and runs nothing; the status records that this run's moment is
   not in progress.
5. **The operator-owed case keeps a clean exit** — where a check cannot run
   because the operator has something to do, such as work that is not
   committed yet, it exits clean and says so. A status meaning no reader is
   needed would be wrong there.

## Alternatives considered

- **A declared first-line marker** — the check's first line is a fixed
  prefix such as `not applicable:`. Rejected; visible to a person, but
  still a string convention, and it forces every check that prints its
  corpus counts before its verdict to reorder its output.
- **Both a status and a marker** — rejected; two conventions to keep in
  step, and a check can emit one without the other, which is a failure
  mode neither has alone.
- **A static disposition where the check is registered** — rejected on
  measurement; membership of the inapplicable set changes with the moment,
  so a value recorded once is wrong on most runs.
- **Leaving it as a judgement reading** — rejected; it is the state the
  moment rule was adopted to remove, arriving one level further in, and a
  reader who meets the same answered line on every run stops reading the
  report it sits in.

## Consequences

- `templates/base/core/quality.md` states the status, its distinction from
  a skip, and the three-way split a summary owes.
- Six shipped checks exit 3: the register-identifier check in
  `base/core/docs.md`; the milestone-coverage, release-ordering,
  changelog-completeness and off-limits-path checks in `base/core/git.md`;
  and the test-visibility check in `base/workflow/quality-gates.md`.
- `tests/run_conformance.py` gains a fifth result and reports it on the
  summary line. On this repository the reading pile fell from twelve to
  four, with four counted as not applicable.
- A consuming project that wires its own runner has one number to read
  rather than a phrase to match, and inherits the distinction between a
  check that cannot apply here and one whose moment is not in progress.
- Status 3 is now reserved across the shipped checks. A check using it for
  anything else would be read as inapplicable.
