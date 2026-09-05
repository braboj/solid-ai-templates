# Issue Formats
[ID: base-issues]

Standard formats for work items in GitHub Issues. Each type has a label,
a title convention, and a body template.

Start with the concrete problem or desired outcome. Use the sections below
as a starting point, not mandatory paperwork: omit empty or irrelevant ones,
and use a short paragraph plus acceptance criteria for a small task.

- Use sentence-case `##` headings with blank lines before the content.
- Keep paragraphs short; use bullets for parallel facts and numbered steps
  for sequences. Reserve checkboxes for observable completion criteria.
- Put commands and exact output in fenced blocks. Link supporting evidence
  beside the claim; put related issues at the end. Use tables for comparisons.
- Keep labels, priority, and milestone in tracker fields rather than repeating
  them in the body. User-story wording is optional, not a required preamble.
- Rewrite the body around the current scope when it changes; preserve useful
  discussion in comments. Avoid accumulating correction preambles and stale
  proposals. Formatting alone requires no ADR, new issue, or automated gate.

---

## Issue types
[ID: base-issues-types]

Every issue MUST have exactly one type and one priority, applied at
creation — never create a ticket unlabeled. The label taxonomy is
project-specific; the at-creation discipline is not.

| Type | When to use |
|------|-------------|
| Bug | Defect in existing functionality |
| Epic | Large initiative spanning multiple tasks |
| Task | Atomic implementable work |
| Spike | Research or exploration — output is a decision |
| Incident | Production outage or degradation affecting users now |

| Priority | Meaning |
|----------|---------|
| P0 | Critical — blocks everything |
| P1 | High — must fix before next milestone |
| P2 | Medium — important but not blocking |
| P3 | Low — nice to have, including trivial |

Priority is severity and nothing else. It MUST NOT encode scheduling —
there is no band meaning "someday", and deferring a high-severity issue
is a scheduling decision recorded elsewhere, not a downgrade to a lower
band.

Platform-specific label implementation (names, colors) is defined in
the platform template (e.g. `platform/github.md`).

The at-creation rule MUST be paired with a conformance check over open
issues, stated as a command with its pass condition — an unlabeled
ticket looks identical to a labeled one, so the discipline decays
silently otherwise. Where the tracker can enforce mutual exclusion natively
(Linear label groups), that is the check; where it cannot (GitHub
labels), state the query and its pass condition in the platform
template. The check reports every open issue not carrying exactly one
type and exactly one of `P0`–`P3`.

---

## System of record
[ID: base-issues-record]

The code host is the system of record. The tracker is a view over it,
chosen for its UI, and MUST be replaceable without losing anything.

- A ticket description MUST NOT be the only copy of anything that
  outlives the ticket. Decisions go in ADRs, rationale and specs in
  `docs/`. The tracker carries status, ordering and assignment — state
  that is worthless after a migration anyway.
- A commit message or PR title SHOULD reference the code-host issue
  number. It lives with the repository and survives a tracker change,
  where a tracker identifier in either becomes a dead reference the
  moment the tracker does.
- A tracker identifier MAY appear in a branch name. Branches are
  deleted after merge, so that reference is ephemeral, and the
  identifier is what drives in-flight status.

Retrofitting this is expensive: every commit message and PR title
written before the rule exists is already permanent.

---

## Deferred work
[ID: base-issues-defer]

When work is genuinely valuable but intentionally deferred — not in the
next milestone, perhaps not the next several — the right home is an
open, unmilestoned issue with explicitly named trigger conditions, not
a TODO line in an ADR or a code comment. The milestone field carries
the scheduling: milestoned means planned into that cut, unmilestoned
means backlog. Do NOT add a deferral label or a named holding milestone
on top — either one duplicates the milestone field, and two carriers
for one signal can disagree without either being wrong.

An empty milestone MUST NOT be read as untriaged. Triage is the type
and severity applied at creation; scheduling is a separate axis, and an
issue is fully triaged whether or not it is scheduled.

- Open the body with the deferral note: "Do not pick up before one of
  the trigger conditions fires." The milestone field records that the
  work is unscheduled; the body records what would schedule it.
- State trigger conditions as concrete, observable events ("a second
  component exhibits pattern X", "badged data runs four weeks without
  pushback") — natural language is fine; naming them is the discipline.
- The open issue is not the watcher, and stating a trigger does not
  create one. Record in the body what would detect the condition, or
  that nothing would — otherwise every pass over the backlog re-runs the
  check by hand to establish that it still has not fired, which is the
  work the ticket was supposed to save.
- Where the issue is also the only thing tracking a drift recorded
  elsewhere — a stale count in a merged record, a divergence held open
  pending this work — say so in the body, so that closing it names what
  loses its tracker instead of dropping it silently.
- Carry acceptance criteria as usual, so the work is sized when picked up.
- Reference the issue from the decision that deferred it (e.g. the ADR's
  Decision section), so the decision stays discoverable from the tracker
  rather than buried where it will be re-litigated or quietly done
  unnecessarily.
- Re-read the unmilestoned set when scoping a cut. Deferral is now the
  absence of a field rather than the presence of a label, so nothing
  surfaces the backlog on its own.
- Scheduling has three states, and the third is the absence of the other
  two: milestoned means planned; unmilestoned with a named trigger means
  deferred; unmilestoned with none means not yet judged, and the groom
  owes it a decision. Do NOT record readiness as a third value: a trigger
  is a question and survives neglect, while readiness is an answer about
  the day it was written, and one nobody has re-read for months asserts
  it as loudly as one verified this morning.
- A groom MAY close an issue whose premise something merged has already
  settled, and this is not a scope edit. Distinguish the two by what the
  measurement found: the claim moved and the work still exists in changed
  form, so annotate and leave it for the implementer; or the premise was
  answered by a merged change, so nothing remains to implement and an
  annotation would wait for an implementer indefinitely.
- Re-verify the trigger against the system before deferring the issue
  again — at triage, at scope selection, or when a session reads the
  backlog and skips it. The body was written once, and a fired trigger
  and an unfired one look identical from the text. A trigger that has
  fired makes the issue open work rather than deferred work, and the
  body MUST be corrected to say so, because the issue's own text is what
  the next reader triages from.

---

## Closing a duplicate
[ID: base-issues-duplicate]

When two issues describe the same work, exactly one MUST survive.

- Before closing an issue as a duplicate or superseded, verify the
  survivor is **open**. If it is closed, reopen it or file a
  replacement first.
- A duplicate chain that terminates in a closed issue silently drops
  the work: every trail leads to a closed record pointing at another
  closed record, and both claim the work is handled elsewhere.
- The surviving ticket carries the better description; the closed one
  carries the triage label and a link to the survivor.
- Reconcile closed issues against work actually shipped at the end of a
  session. Two closures made in opposite directions are each
  individually reasonable and invisible until something compares the
  tracker against the tree.

---

## Epic

A large initiative too big for one task. Tracks progress via child issue
checklist.

**Title:** descriptive goal (no prefix — the `epic` label identifies the type)

```markdown
## Goal

[One sentence — what does success look like?]

## Tasks

- [ ] #XX — task description
- [ ] #YY — task description

## Definition of done

[Measurable criteria for closing]
```

**Rules:**
- Every epic MUST have a tasks checklist with issue references
- Check off children as they close — do not let checkboxes go stale
- Close the epic when the goal is met, even if stretch items remain
- Epics span phases — do not force them into one milestone

---

## Task

An atomic, implementable unit of work. One task = one branch = one PR.

**Title:** descriptive action (no prefix — commit messages carry the
`feat:/fix:/data:/docs:/chore:/refactor:/test:` prefix, not issue titles)

```markdown
## Problem

[Current limitation and who it affects]

## Proposed change

[Desired behavior; a before/after example when useful]

## Acceptance criteria

- [ ] [Observable behavior 1]
- [ ] [Observable behavior 2]
```

**Rules:**
- Scoped to a single concern — do not mix refactoring with features
- The agent SHOULD be able to complete it in one conversation turn
- If a task needs multiple sub-tasks, it is an epic
- Acceptance criteria MUST be verifiable (build passes, page renders, score
  matches)

---

## Bug

A defect in existing functionality.

**Title:** what is broken (no prefix — the `bug` label identifies the type)

```markdown
## Problem

[Observed failure and user impact]

## Expected

[What should happen]

## Reproduce

1. [Step 1]
2. [Step 2]
3. [Observed result or error]

## Environment

[dev/preview/production, browser, branch]
```

**Severity guide:**

| Level | Meaning | Example |
|-------|---------|---------|
| critical | Page broken, data loss, deploy blocked | Blank page, build fails, wrong data shown |
| major | Feature does not work but site is usable | Filters return 0 results, sort broken |
| minor | Works but wrong behavior in edge case | Discontinued item not sorted last |
| trivial | Visual only, no functional impact | Alignment off, color slightly wrong |

**Rules:**
- Every bug MUST include reproduction steps
- Environment MUST specify dev, preview, or production
- Do not open a bug without attempting to reproduce it first

---

## Incident

A production outage or degradation affecting users now. Different from a
bug — a bug is a defect you discover, an incident is something burning.

**Title:** what is down (no prefix — the `incident` label identifies the type)

```markdown
**Status:** investigating | identified | mitigating | resolved

## Impact

[Who is affected, how severely]

## Timeline

- [HH:MM UTC] — [event]
- [HH:MM UTC] — [event]

## Root cause

[What caused it — fill in after identified]

## Resolution

[What fixed it — fill in after resolved]

## Prevention

[What changes prevent recurrence — fill in after postmortem]
```

**Rules:**
- Only critical or major — if it is minor, it is a bug, not an incident
- Update the status field as you work through it
- Timeline MUST capture the sequence of events
- Prevention is mandatory — every incident MUST produce a change
- Create a follow-up task or ADR from the prevention section

---

## Spike

Research or exploration where the output is a decision, not code.

**Title:** the question being investigated (no prefix — the `spike`
label identifies the type)

**Format:** state the question, the decision it informs, and the required
evidence. An ADR is an output only when the architectural threshold is met.

```markdown
## Question

[Specific uncertainty to resolve]

## Context

[Decision blocked and relevant evidence already available]

## Deliverable

- [ ] Recommendation supported by the relevant evidence
- [ ] Alternatives and material tradeoffs, including doing nothing
```
