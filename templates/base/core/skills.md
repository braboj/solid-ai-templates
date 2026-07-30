# Base — Agent Skills

[ID: base-skills]

## Principle

- A skill is production instruction, not a note. It ships, it drifts, and it
  needs the same discipline as code
- Every skill MUST be one of two kinds: **orchestrating** or **atomic**
- A rule that two skills need MUST live in one shared module, not in both
- A skill's instructions MUST be testable, and the tests MUST come from
  failures that actually happened

## The two kinds

**Orchestrating** skills own a workflow: the step order, the inputs, and the
handoffs. They delegate each step and they do not restate rules.

**Atomic** skills do one job with one output contract and delegate nothing.

A skill that is neither is a monolith. Two signs:

- It asks the user which of several things they meant, then inlines all of
  them. That is a dispatcher with the implementations pasted underneath it;
  split it into a router plus one atomic skill per branch
- It describes work another skill already implements. State the delegation and
  wire it, or the two descriptions drift apart

## Rules live in shared modules

Self-contained skills are the obvious design and the wrong one. Each reads
completely on its own, and that is exactly what lets two copies of the same
rulebook diverge without anyone noticing.

- A rule needed by more than one skill MUST move to a shared module; the
  skills point at it
- A skill MUST NOT restate a rule it points at. Restating is how the copies
  separate
- Where a skill and a module disagree, the module wins and the skill is the bug
- Split modules by **rate of change and audience**, not by size. Rules that
  change when the product changes do not belong with rules that never change

**Failure this prevents.** In one repository the writing skill and the scoring
skill each carried the same rulebook. The scorer's copy had grown six rules the
writing skill never received, so work was produced without rules it was then
graded against. Neither file was wrong on its own.

## A prose rule does not enforce itself

Writing "re-verify this before use" into a skill does not cause verification.
The instruction runs only if something runnable reaches it.

- A rule that can rot MUST have a check in the verification step, not only a
  sentence in the guidance
- Prefer a command whose output is a finding (`grep`, a linter, a script) over
  a paragraph asking for judgement
- Timestamp facts that expire, and say where the current value comes from

**Failure this prevents.** A catalog figure sat stale in a skill for months,
directly above a rule instructing the reader to re-verify it against the live
source. The rule was correct, was never executed, and the wrong number shipped
into published work.

## Progressive disclosure

A skill's entry file is loaded whenever the skill triggers; bundled files are
read only on demand. That makes the entry file the expensive part.

- Keep the entry file to an overview that points at detail
- References MUST be one level deep from the entry file. A reference that only
  another reference points at gets previewed rather than read, so the agent
  silently works from part of it
- A reference over ~100 lines MUST open with a table of contents, so a partial
  read still shows the full scope
- When a shared module absorbs a reference, link that reference directly from
  every skill that needs it. Routing it through the module alone pushes it to
  the second level

## Evaluating skills

Skills degrade agent behaviour when they trigger wrongly, conflict with each
other, or instruct poorly. Five dimensions are worth measuring:

| Dimension | Question |
| --- | --- |
| Triggering accuracy | Fires for the right requests, stays quiet for others |
| Coexistence | Adding it does not steal another skill's triggers |
| Isolation | Works correctly on its own |
| Instruction following | The agent actually does what it says |
| Output quality | The result is correct and useful |

Rules:

- Every case MUST cite the observed failure it came from. A case with no
  failure behind it is an imagined requirement, and imagined requirements are
  what evaluation exists to prevent
- Cover negative cases. Where every skill's description names the same domain,
  a false trigger is likelier than a missed one
- Adding a skill MUST add its coexistence cases. A new description competes
  with every existing one for the same words, and nothing surfaces that until
  something tests it
- Test on every model the skills will run under. Effectiveness varies by model

**Two findings worth inheriting.**

Indirection survives smaller models better than expected: an instruction to go
read three modules first was followed at every tier tested. What degraded was
rule *application*, not rule *loading*. The same rule sat in context on both
runs and only the stronger model applied it. Do not assume a skipped rule was
never read.

Subagents cannot measure triggering or coexistence. A subagent does not
reliably carry the parent session's skill registry, so "no skill loaded" is
ambiguous between the skill correctly staying quiet and the skill never having
been available. **Negative cases survive this** (both causes give the same
right answer); positive cases do not, and need a fresh top-level session.

## Shared namespaces have no owner

Where skills or their outputs write into one flat shared directory, no file has
an owner, and the component that stops using a file is not the component that
owns it.

- Before deleting from a shared namespace, search every consumer for the name
- Prefer per-component directories. Scoping is the structural fix; a naming
  convention is only a mitigation
- Where a shared namespace is unavoidable, prefix on write and check for
  collisions mechanically

## MUST checklist

- [ ] Every skill is orchestrating or atomic, and says which
- [ ] No rule appears in two skills
- [ ] Every rule that can go stale has a runnable check
- [ ] Every reference is one level deep from an entry file
- [ ] Every reference over ~100 lines opens with a table of contents
- [ ] Every evaluation case cites the failure it came from
- [ ] Negative and coexistence cases exist, not only positive ones
- [ ] Skills tested on every model they run under
- [ ] Deleting a skill leaves no dangling reference in docs, config, or other
      skills

## Related

- `templates/base/core/agents.md` — the agent instruction file these support
- `templates/base/core/testing.md` — evaluation as a testing discipline
- `templates/base/core/review.md` — reviewing agent-authored work
