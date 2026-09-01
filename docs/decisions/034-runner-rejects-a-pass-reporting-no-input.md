---
id: "034"
status: Accepted
date: 2026-09-01
category: tooling
supersedes: []
superseded_by: []
---

# ADR-034: The runner rejects a pass that reports no input

## Context

A check that reports only what it found reads identically when its corpus
empties and when the tree is clean. Both print nothing and exit zero. The
rule that a check MUST state what it inspected, not only what it found, is
shipped in the templates and enforced on template checks by the
conformance runner. It was not enforced on this repository's own smoke
suite, where 25 of 26 checks reported only failures.

The gap was not theoretical. One check passed with its directory list
pointed at a renamed path and again with the list emptied, because a
missing directory was skipped with a bare `continue`. Another passed by
looping over an empty stack list. A third — the only one carrying a
reached-nothing guard — had a matching pattern that could see 100 of the
341 declared section IDs, and reported green while the rule it enforces
was violated in three shipped artifacts.

Adding the counts to all 26 closes today's instance. It does not close the
class: the twenty-seventh check is written by someone who has not read
this, and a suite that asks every check to remember a contract gets checks
that do not.

## Decision

1. **Every check reports its inputs** — each check records what it
   reached, and the counts print under its verdict on every run, whatever
   the verdict. A count below its declared floor is a failure

2. **The runner enforces the contract** — a check that would pass while
   reporting no inputs is failed where it is called, not where it is
   written. A failing check has already said something, so only a silent
   pass is rejected

3. **A check reports the inputs it has** — where a check builds its own
   fixture rather than reading the tree, what it reports reaching is the
   assertions it ran against that fixture. A constant is a weak input
   count and still distinguishes a check that ran from one that returned
   early

4. **An absent corpus root is a finding, not a skip** — a directory,
   file or listing a check is pointed at and does not find MUST be
   reported. The count reaches zero either way; only the finding says
   why

## Alternatives considered

- **Leave enforcement to each check** — rejected; it is the arrangement
  that produced 25 checks without it. The contract holds only where
  nobody has to remember it

- **A twenty-seventh check that inspects the other twenty-six** —
  rejected; it runs every check a second time to ask a question the
  runner can answer for free as each one returns, and it is itself a
  check that can be narrowed until it sees nothing

- **Report the counts without failing on zero** — rejected; a number
  nobody is required to read is the state the suite was already in. The
  reader who would notice a count drop to zero is the reader who was
  already reading closely

- **A floor on every count** — rejected as stated; some counts are
  legitimately zero in a tree with nothing wrong, and a floor there
  trains the reader to ignore the failure. The floor is declared per
  count, and a count whose emptiness the check already asserts on
  carries none

## Consequences

- A check may return its failures, or a `(failures, notes)` pair. Both
  shapes are accepted, so a check gains the report without every other
  one changing
- A check added later cannot reintroduce the class: it fails on its
  first green run until it reports something
- Reports carry an `Inspected` block, so a count that moved between two
  runs is recoverable after the fact rather than only on screen
- The counts are not findings. A reader scanning for failures now scrolls
  past roughly fifty lines of them, and the suite's output grew by half
- `tests/INDEX.md` states the contract once for every spec rather than
  each spec restating it
