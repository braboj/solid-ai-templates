# Issue Formats
[ID: base-issues]

Standard formats for work items in GitHub Issues. Each type has a label,
a title convention, and a body template.

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

`P4` is not a severity. It marks work deliberately deferred, and MAY
accompany any of `P0`–`P3` — deferring a high-severity issue is a
scheduling decision, not a downgrade. Every issue MUST carry exactly
one of `P0`–`P3`; `P4` is optional and additional.

Platform-specific label implementation (names, colors) is defined in
the platform template (e.g. `platform/github.md`).

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
open issue carrying the `P4` deferral marker and explicitly named
trigger conditions, not a TODO line in an ADR or a code comment. `P4`
records that the deferral is deliberate rather than an untriaged
oversight. Do NOT park the work in a named holding milestone instead —
a lane's meaning is lost when the milestone is closed or deleted, while
a label travels with the issue.

- Open the body with the deferral note: "Do not pick up before one of
  the trigger conditions fires."
- State trigger conditions as concrete, observable events ("a second
  component exhibits pattern X", "badged data runs four weeks without
  pushback") — natural language is fine; naming them is the discipline.
- Carry acceptance criteria as usual, so the work is sized when picked up.
- Reference the issue from the decision that deferred it (e.g. the ADR's
  Decision section), so the decision stays discoverable from the tracker
  rather than buried where it will be re-litigated or quietly done
  unnecessarily.

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

## Out of scope
[What this epic does NOT cover]

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
Embeds a user story line for user context.

**Title:** descriptive action (no prefix — commit messages carry the
`feat:/fix:/data:/docs:/chore:/refactor:/test:` prefix, not issue titles)

```markdown
As a [user type], I want [capability] so that [benefit].

## What
[Clear description of the change]

## Why
[Motivation — which epic does this serve?]

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
**Severity:** critical | major | minor | trivial

## Expected
[What should happen]

## Actual
[What happens instead]

## Reproduce
1. [Step 1]
2. [Step 2]
3. [Result]

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
**Severity:** critical | major
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

**Format:** use the task format. The acceptance criteria describe what the
spike should produce (an ADR, a recommendation, a prototype).

```markdown
As a [role], I want to understand [topic] so that [decision can be made].

## What
[Question or area to explore]

## Why
[What decision is blocked without this research?]

## Acceptance criteria
- [ ] ADR documenting the decision
- [ ] Recommendation with alternatives considered
```
