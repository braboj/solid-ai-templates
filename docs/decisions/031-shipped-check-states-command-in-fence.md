---
id: "031"
status: Accepted
date: 2026-08-29
category: templates
supersedes: []
superseded_by: []
---

# ADR-031: A shipped check states its command in a fenced block

## Context

The templates embed runnable checks beside the rules they verify, and
this repository runs them against itself. The runner extracts fenced
blocks and requires every one to carry a disposition, so a check added to
a template cannot arrive unexamined.

That guarantee holds only over checks the runner can see. Nothing said
which form a check must take, and one was written in running prose:

> Commit a `.gitattributes` at the project root with `* text=auto` ...
> Verify with `git ls-files --eol` -- no committed file reports `i/crlf`

That is a command and a pass condition, which is what the pair-check rule
asks an author to supply. It was simply not in a fence, so nothing
extracted it, nothing ran it, and the rule was unenforced here. A
conformance run reporting 19 passed and 0 failed coexisted with a
violated rule on the same tree -- the failure the runner exists to
prevent, one level up.

The runner already reconciles the runnable subset against every fenced
block, because an extraction that silently under-counts looks identical
to a clean one. That reconciliation is bounded by the fence: it cannot
report a check it has no way to count. The completeness of the whole
mechanism therefore rested on an assumption about how authors typeset
their checks, and the assumption was untrue.

A survey found a second instance of a different shape. A rule stated
`Check: install the project alone, then execute every file under
examples/`, with a pass condition beside it. Its command is prose. There
was nothing to move into a fence, and an author reading a rule that says
only "put the command in a fence" would see nothing to do.

## Decision

1. **The command MUST sit in a fenced block.** Prose introduces the check
   and carries its pass condition beside the fence; the runnable form
   lives inside one. A command typed into a sentence cannot be extracted,
   counted or run, so the rule naming it is unenforceable by any tool.

2. **Naming no command states no check.** A sentence describing an action
   reads as a check and is not one. The fence requirement does not reach
   it, because there is nothing to move. Write the command first, then
   fence it.

3. **A tool reporting how many checks it ran MUST also report how many it
   could not see.** A count taken over the parseable form alone is
   complete only by assumption. The rule carries a check that scans
   running prose for a verification phrase paired with a backticked
   command, skipping fenced lines and table cells and allowing a
   five-line window for a pass condition stated beside its own fence.

## Alternatives considered

- **Fence the one offending check and stop** -- rejected; it fixes the
  instance and leaves the class. Nothing would tell the next author which
  form to use, and nothing would report how many prose checks exist.
- **Extract inline checks too** -- rejected; more faithful to what
  authors write, but the delimiters are prose and the extraction becomes
  guesswork. That contradicts locating a block by a string only its body
  contains, and it would trade a countable gap for an uncountable one.
- **Require the fence without a detector** -- rejected; a stated
  constraint with no check is the decoration this repository's own
  pair-check rule exists to forbid.
- **Treat the prose form as acceptable where the command is short** --
  rejected; the length of a command has no bearing on whether a tool can
  find it, and a size threshold is a judgement no check can apply.

## Consequences

- Both instances are now in the runnable form. The line-ending check runs
  against this repository, which is what makes a missing `.gitattributes`
  mechanically detectable rather than found by eye.
- The example-execution check gained a command with a placeholder runner,
  and a pass condition treating a count of zero as a failure rather than
  a clean run.
- The runner now reports the output a manual check produced. Its
  documented behaviour already claimed this and its implementation did
  not, so a manual check ran, saw something, and told nobody.
- The conformance suite goes from 44 registered blocks to 47, and from 19
  checks run to 22.
- `CLAUDE.md` section 2.7 carries the authoring rule, so it applies on
  every template turn.
- A future check added in prose is a finding rather than an invisible
  gap, and the count of prose checks is reported on every run.
