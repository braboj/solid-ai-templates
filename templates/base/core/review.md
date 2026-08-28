# Base — Peer Review

[ID: base-review]

## Principle

- All code MUST undergo a peer review before merging
- The reviewer is accountable for what gets merged
- The developer is responsible for the code they write
- Reviews have priority over your own development — a blocked reviewer
  blocks the team

## Priority order

Apply the following order when reviewing, from most to least critical.
Use `templates/base/core/quality.md` (and any language-specific quality template
such as
`templates/base/language/typescript.md`) as the standard for items 2–4.

1. **Security exposure** — anything that could be exploited, any credential
   or license problem
2. **Functional correctness** — paths that produce wrong results, unhandled
   failures, or race conditions
3. **Clarity** — obscure names, deep nesting, high cognitive complexity,
   boolean flag parameters
4. **Convention compliance** — code that deviates from agreed project patterns

## MUST checklist

- [ ] No credentials, tokens, or sensitive values appear anywhere in the
      committed files
- [ ] Every failure path is explicitly handled — no silent catches, no
      swallowed exceptions
- [ ] Any new dependency carries a license compatible with the project policy
- [ ] Significant logic or architectural decisions are captured in documentation
- [ ] Existing documentation reflects the state of the code after this change
- [ ] Every changed section was re-read whole, not just the changed line — a
      sentence is correct only in relation to its neighbours, and each one
      reads fine alone, so a diff review cannot catch the contradiction
- [ ] Every claim the text makes **about itself** ("each section covers X",
      "the table below compares N criteria") was verified by counting or
      grepping the thing claimed — `grep -c` the sections, count the rows —
      not by reading. Scope both checks to changed sections, so the cost
      stays proportional to the diff

## MUST checklist — state and boundaries

- [ ] If the change touches shared browser or framework state (history,
      URL, localStorage, global context), verify what else depends on that
      state — review the change in the context of the framework contract,
      not in isolation
- [ ] URL parameters and query strings are treated as untrusted external
      input — validate before destructuring, indexing, or using as keys
- [ ] Refactoring preserves behavior for ALL code paths — if a function
      handles N cases, verify N × directions/modes; extracting a helper
      must not silently change edge-case behavior (null handling, sort
      direction, boundary values)

## CI signals

- [ ] When CI fails, separate **infra failures** (the action could not
      run — network, missing release, broken pinning, runner OOM) from
      **diff failures** (the check ran and produced a negative signal on
      the diff). An infra failure is a signal about the workflow, not
      the PR — surface it honestly in the merge decision rather than
      retrying or ignoring it

Practical guidance:

- On a red check, read the log before calling the PR green or red
- If the failure is infra (`curl 404`, `docker pull` timeout, package
  not found), file a separate task to fix the workflow and note it in
  the merge call
- Do NOT retry-until-green silently — that masks the infra problem
- Do NOT push past it with `--no-verify` or an admin merge unless the
  maintainer explicitly accepts the risk

## SHOULD checklist

- [ ] Non-trivial functions have a unit test for each relevant variant
- [ ] Code coverage does not decrease
- [ ] Lint errors/warnings do not increase
- [ ] Third-party dependencies are necessary, understood, and well-maintained
- [ ] Code is simple — no new abstraction without two or more call sites,
      no new dependency without a documented reason
- [ ] Numerical comparison gates (render-match scoring, calibration
      tolerances, visual-regression diffs) lock the values they sample,
      not the shape between samples — on render-producing pipelines
      (charts, diagrams, illustrations) pair them with manual visual
      review; a passing numerical gate is necessary, not sufficient
- [ ] A score that sums or averages several components draws them from
      genuinely independent variables, not algebraic transforms of one
      another (`x`, `x/2`, `1/x`). Scale-invariant aggregation (z-scores,
      ranks) collapses such components onto one axis, silently
      re-weighting it while the code and the docs still claim independent
      contributions. Where components share a quantity, drop the
      redundant ones or state the real weighting

## Structure audit

A code review checks changed files. A structure audit checks project
completeness. Run a structure audit after:

- New project setup
- Framework or stack migration
- Adding a major layer (backend, CI/CD, infrastructure)
- Before a release milestone

Verify every MUST from:

- `templates/base/core/docs.md` — standard documents (README, ONBOARDING,
  PLAYBOOK, ADRs)
- `templates/base/core/readme.md` — README has all 9 required sections
- `templates/base/core/git.md` — .gitignore, README exist
- The relevant frontend or backend layer template — required assets,
  config files, SEO files
- The relevant stack template — framework-specific files and conventions

When a section contains multiple MUST sub-clauses, verify each sub-clause
independently — do not pass the section as a whole. For example,
`templates/base/core/readme.md` Usage requires both usage examples AND expected
output
per example — these are two separate checks.

SHOULD also check:

- No substantial duplication across sibling components — if two or more
  components share the same code, extract a shared module

## Verifying a filed issue before implementing it

An issue is written against the tree as it stood on the filing date. By the
time it is picked up the tree has moved — sometimes through work that closed
a neighbouring issue, sometimes because the rule it argues from never existed
in this project at all. An issue describing a gap is evidence the gap existed
when it was filed, not that it exists now.

The tree is not the only thing that moves. A decision accepted since the
filing date can relocate the rule the issue proposes, and another session can
already be implementing it — neither is visible from the issue, and neither is
a defect in the issue.

None of these shapes means the issue was wrong to file. Each produces subtly
wrong work when implemented from the text alone, and the wrongness is
invisible afterwards: the change is coherent, the tests pass, and it addresses
something that was not the problem — or re-does something already in review.

- [ ] Re-read the target file for existing coverage before writing anything.
      A rule that landed since the filing date may already say most of it
- [ ] Verify anything the issue cites as existing — a rule, a file, a command,
      a behaviour. An issue written from a downstream project may quote that
      project's rules as though they were this one's, and implementing it as
      written cites a rule that is not there
- [ ] Run what the issue proposes against the tree before adopting it. A
      proposed constraint that would flag working code is a wrong rule, not
      an under-enforced one
- [ ] Restate the scope before starting if it moved. Narrower than filed
      finishes sooner; wider needs saying before the work rather than after
- [ ] Check the open pull requests for one that already closes it. An issue
      stays open and unassigned while a complete implementation sits in
      review, and the only link between them is in the pull request body
- [ ] List the decision records accepted since the filing date and confirm
      none of them moves what the issue proposes. An issue is correct as of
      its filing date, and the tree it was measured against is not the tree
      it will land in

Five shapes, all of which change what gets built:

| Shape | What it looks like |
|-------|--------------------|
| Narrower than filed | The section already covers most of it; the work is two bullets, not a rewrite |
| Wider than filed | The defect the issue names is present in two siblings it does not mention |
| Wrong as filed | The rule it proposes, run against the tree, flags code that is correct |
| Already in flight | The issue is open and unassigned while a complete implementation sits in an open pull request |
| Superseded as filed | A decision accepted since the filing date moved the rule, the home, or the mechanism it names |

The last two shapes are mechanically checkable, and both fail the same way:
an empty result reads as a clear field whether the query found nothing or
reached nothing.

```bash
gh pr list --state open --limit 100 --json number,body --jq 'length as $n | "open pull requests inspected: " + ($n|tostring), (.[] | select(.body | test("[Cc]loses #<N>([^0-9]|$)")) | "already in flight: #" + (.number|tostring))'
```

Pass condition: the reported count matches the open pull requests the tracker
shows, and nothing follows it. A count of zero where the tracker lists open
pull requests means the query or the repository context is wrong rather than
the field being clear. The trailing character class is load-bearing — without
it, a search for issue 104 matches a body closing 1041.

```bash
git log --since=<filing date> --name-only --format= -- docs/decisions/ | sort -u
```

Pass condition: the command lists the decision records added or amended since
the issue was filed, and none of them moves the rule, the home, or the
mechanism the issue names. Run it once without `--since` to confirm the path
resolves, because a mistyped directory and a genuinely quiet window print the
same empty listing. Where a record does move it, implement the decision and
state the deviation from the filed acceptance criteria in the pull request:
the issue is not wrong and does not need re-filing, its criteria need reading
against the record that superseded them.

## Verifying a finding before reporting it

A finding is a hypothesis until it is demonstrated. Reporting a hypothesis as
a defect costs the author more than missing it, because each one has to be
disproved by hand. A finding that cannot be demonstrated MUST be labelled as
unverified rather than presented alongside demonstrated ones.

What you owe a finding depends on how it was produced.

### From reading

- [ ] Reproduce the defect before reporting it — run the path, not the
      argument that the path is wrong
- [ ] When a reproduction contradicts a passing test, read the test before
      concluding the code is wrong. A test that pins surprising behavior is
      usually documenting a decision, and its comment is where the reason
      lives

### From a measurement

A tool that runs cleanly and returns a plausible number is the most convincing
way to be wrong, and a zero is the most convincing number it can return — a
silent failure and a real absence print the same thing.

- [ ] Confirm the tool measures the unit the rule is written in — bytes are
      not characters, `wc -c` is not `wc -m`, disk size is not size on disk
- [ ] Confirm the tool measured the **scope** the claim is about. Many tools
      silently narrow to a diff, a changed-files set, a sample, or one
      partition when run in a pull-request or incremental context, and report
      a count that is correct for that subset. A baseline claim about a whole
      codebase MUST come from a whole-codebase run
- [ ] Record which mode produced any number you keep. A figure with no scope
      attached is read as a baseline by whoever finds it next, and an
      incremental run reporting zero on a tree nobody has ever scanned is
      evidence that no baseline exists, not evidence that it is clean
- [ ] Hand-check one flagged item. If the hand-count disagrees with the tool,
      the tool is measuring something else
- [ ] Produce a count that carries a finding twice, by different means.
      Agreement between two tools is the check; one tool run twice is not
- [ ] Verify a zero by finding one positive by hand, and prefer a tool whose
      failures are loud over one that can exit clean on an unsupported
      feature. Nothing in the output separates a silent tool failure from a
      genuine absence, and the absence is the more alarming finding of the two

### From an extraction

Extraction tools are silently partial: a parser walks the node types it knows
and drops the rest, so "X is missing" often means "my extractor does not
traverse the structure X lives in".

- [ ] Before asserting an element is **absent**, cross-check the raw artifact
      itself, not just the tool's output
- [ ] Sanity-check coverage — compare extracted size against the raw artifact
      and confirm known-present elements survive the round trip
- [ ] Scope the claim to what was inspected: "not verifiable from the
      extract", never "missing". Absence of evidence from a lossy tool is not
      evidence of absence

### From a probe running as the wrong principal

A request's result depends on who makes it. A probe run anonymously, or with a
different credential type than the real consumer uses, answers a different
question than the finding claims to answer, and the obvious follow-up check
usually confirms the wrong answer rather than exposing it.

- [ ] Name the principal the finding is about — anonymous visitor, signed-in
      user, service account, CI runner — and confirm the probe ran as that
      principal, not merely as something authenticated
- [ ] Check the credential **type** matches, not only its presence. Cookie
      sessions, bearer tokens, signed URLs and mTLS are not interchangeable,
      and an endpoint honouring one commonly ignores another. A token added to
      a cookie-authenticated endpoint reproduces the anonymous result and
      reads like confirmation
- [ ] Where the probe cannot assume the consumer's identity, scope the claim
      to the principal tested — "returns 404 to an anonymous client", never
      "is broken"

### From an agent or subagent

A finding reported by an agent is a lead, not evidence. Verify it against the
source before acting on it or repeating it to anyone else.

- Check the claim against the file, the commit, or the upstream document that
  would settle it, not against the plausibility of the wording
- "Could not confirm" is not evidence of absence. Distinguish a verified
  negative from a failed lookup, and say which one you have
- A finding confirmed by several agents is still one finding. Independent
  agents share the same blind spots and can agree on the same wrong answer
- When a finding turns out to be wrong after you have passed it on, correct it
  plainly and name what the check actually showed

When a finding contradicts an existing verified record, reconcile the two
before changing anything:

- Check whether both are reading the same artifact. Different pages,
  endpoints, API versions, or product tiers routinely disagree, and each may
  be locally correct
- Prefer the source carrying more specific evidence — a record citing a file
  with per-item detail outranks a summary citing a README
- Treat "could not confirm" as a request to reconcile, never as a licence to
  delete
- Dispatch with the existing record attached, asking the agent to
  **reconcile** rather than re-derive. An agent told only "verify this claim"
  surfaces a different source; one told what was previously found, and where,
  surfaces a genuine change
- Record the reconciliation. If it reverses a documented decision, say so and
  why, in the artifact that documented it

Applies equally to the reviewer's own tooling: a grep that returns the expected
answer for the wrong reason is the same failure in a cheaper form.

## Deviations

- Deviating from a SHOULD rule requires a written explanation in the pull
  request
- Deviating from a MUST rule requires explicit sign-off from a designated
  approver before the change can land
