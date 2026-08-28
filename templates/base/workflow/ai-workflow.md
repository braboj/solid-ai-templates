# AI-Assisted Development Workflow
[ID: base-ai-workflow]

How to structure work when collaborating with AI coding agents. Covers the
project lifecycle, work item hierarchy, and practices that maximize agent
effectiveness.

## Lifecycle Phases

### 1. Spike (Explore)

Conversational research to understand the problem space and generate
recommendations.

**What the human does:**
- Defines the question or area to explore
- Validates findings against domain knowledge
- Decides whether to proceed

**What the agent does:**
- Researches codebases, documentation, and web sources
- Compares alternatives with tradeoffs
- Produces a recommendation with rationale

**Output:** A decision or ADR (Architecture Decision Record) documenting the
choice and why.

**Anti-pattern:** Skipping the spike and jumping to code. The agent will build
whatever you ask — the question is whether it's the right thing to build.

### 2. Prototype

A throwaway implementation to validate feasibility and UX direction.

**What changes with AI:**
- Prototypes are nearly free — an agent can build one in a single session
- The bottleneck shifts from building to deciding. Have the conversation about
  what you want before generating code
- Prototype code should be disposable. Don't polish it — test the concept, then
  rebuild properly

**Output:** A working demo the stakeholder can interact with. Keep or discard
based on feedback.

**Anti-pattern:** Polishing the prototype into the product. Prototype code
carries technical debt from speed-first decisions.

### 3. Design

Define the MVP scope, data model, architecture, and conventions.

**What to produce:**
- Architecture Decision Records for non-obvious choices
- Data model (types/interfaces)
- Page/component structure
- Convention file (CLAUDE.md or equivalent) so the agent follows project rules
  across sessions

**Key principle:** The convention file is the agent's long-term memory. Anything
not written down will be forgotten between sessions. Invest time in CLAUDE.md —
it pays back on every future conversation.

### 4. Development

Iterative implementation using epics, stories, and tasks.

**The loop:**
1. Human picks the next work item
2. Agent implements on a branch
3. Human reviews (preview, tests, code)
4. Merge or adjust
5. Repeat

**What works well:**
- One task per conversation turn — keeps context focused
- Branch per feature — clean git history, easy to revert
- Build and test after every change — catch issues immediately
- Commit messages explain why, not what

**What doesn't work:**
- "Make it better" — too vague, agent has no target
- Multiple unrelated changes in one conversation — context pollution
- Skipping the build step — silent failures accumulate

### 5. Deploy

Set up CI/CD, configure hosting, verify in production.

**Agent role:** Write the workflow files, configure build steps, troubleshoot
deployment failures.

**Human role:** DNS, domain registration, secrets, access tokens — things that
require account access.

### 6. Monitor

Track errors, performance, and user feedback.

**Agent role:** Set up monitoring config, analyze logs, investigate reported
issues.

**Human role:** Watch dashboards, collect user feedback, prioritize fixes.

---

## Work Item Hierarchy

### Epic

A large initiative spanning multiple sessions. Too big for one task.

**Good epic:** "Genre Scoring System" — clear goal, multiple components,
measurable completion.

**Bad epic:** "Make the site better" — no clear scope or completion criteria.

**Rules:**
- Every epic needs a checklist of child issues
- Track completion by checking off children as they close
- Epics span phases — don't force them into one milestone
- Close the epic when the goal is met, even if stretch items remain

### User Story

Describes a capability from the user's perspective. Guides the agent toward the
right outcome.

**Format:** "As a [user type], I want [capability] so that [benefit]."

**Examples:**
- "As a budget photographer, I want to sort lenses by optical quality and price
  so that I can find the best value."
- "As a nightscape shooter, I want to filter lenses by coma score so that I only
  see lenses suitable for astrophotography."

**Why stories matter for AI agents:** Agents take instructions literally. A user
story gives the agent the user's perspective, not just a technical
specification. This produces better UX decisions when the agent has latitude.

### Task

An atomic, implementable unit of work. One task = one branch = one PR.

**Good task:** "Add OQ column to Lens Explorer table and mobile cards, computed
from weighted optical field average."

**Bad task:** "Improve the lens explorer."

**Rules:**
- Scoped to a single concern — don't mix refactoring with features
- Includes acceptance criteria or a clear definition of done
- Assignable to a milestone and epic
- The agent should be able to complete it in one conversation turn

**Task types:**
- `feat:` — new functionality
- `fix:` — bug fix
- `refactor:` — code improvement, no behavior change
- `chore:` — tooling, config, dependencies
- `docs:` — documentation only
- `data:` — data additions or corrections
- `test:` — test additions or improvements

### Bug

A defect in existing functionality.

**What to include:**
- What you expected vs what happened
- How to reproduce (which page, which action, dev or preview)
- Screenshots or error messages if available
- Browser/environment if relevant

**Why context matters for AI agents:** "The page broke" forces the agent to
guess. "The wiki filter shows 0 entries on preview after the Content Collections
migration" lets the agent diagnose immediately.

---

## Practices for Agent Effectiveness

### Write things down
[ID: ai-workflow-write-down]

The agent has no memory between sessions. Persistent context lives in:
- **CLAUDE.md** — project conventions, stack, commands, rules
- **ADRs** — architecture decisions with rationale
- **Issue descriptions** — detailed enough for the agent to act without asking
- **README** — project overview and setup

If you find yourself repeating instructions, add them to CLAUDE.md.

### Doc placement decision tree
[ID: ai-workflow-doc-placement]

When the agent learns a new rule, convention, or fact worth persisting,
it MUST consider all valid homes before saving — not default to
CLAUDE.md or memory. Evaluate in priority order:

1. **Code / JSDoc / docstrings** — naming, typing, or invariant rules
   a developer reads while editing the relevant code
2. **ADR** — architectural decisions with alternatives weighed
3. **README** (project or package) — discoverable user-facing setup,
   usage, or capability
4. **PLAYBOOK** — operational workflow (commands, recipes)
5. **CLAUDE.md** — only if the agent MUST apply the rule on every turn
6. **Memory** — only for user / feedback / project / reference facts
   that do not fit a code-side home

Application rule:

- If the right home is obviously memory (user preference, agent
  behaviour) or obviously CLAUDE.md (every-turn rule), the agent MAY
  act without asking
- Otherwise the agent MUST ask one question — "the right home for
  this looks like X — agree?" — and act on the user's call
- The agent MUST NOT silently default to CLAUDE.md or memory

This prevents CLAUDE.md and memory from silently absorbing content
that belongs in code, ADRs, READMEs, or PLAYBOOK — which dilutes
attention on rules that genuinely need to fire on every turn.

### Agent output style
[ID: ai-workflow-output-style]

Output to the user MUST be terse and scannable. Optimize for the
reader skimming the screen, not the writer covering all bases.

- Short sections with clear headings
- Bullets over paragraphs; one sentence per point where possible
- Tables and lists over prose when comparing options
- State the recommendation directly; reserve rationale for when asked
- Skip throat-clearing ("Good call", "Fair enough", "Great question")
- Skip restating the problem — the user already knows it
- Match the response shape to the request: a one-line question gets
  a one-line answer, not a structured document

The aim is the reader's time, not the writer's thoroughness.

### Match document convention
[ID: ai-workflow-match-convention]

Before appending to or editing any document with an established
format (dev journal, ADRs, README, changelog, specs-log,
scoring-log, etc.), the agent MUST read the most recent 1–2 prior
entries and copy their skeleton: heading levels, section order,
label style (e.g. `#### PRs` vs `**PRs:**`), bullet vs paragraph
form, and presence/absence of preamble.

This applies even when a project's CLAUDE.md or PLAYBOOK names the
required *content* but not the exact *format* — the prior entry is
the authoritative structural template. Do not let stylistic choices
from the current chat session bleed into documents with their own
convention.

If the prior format is genuinely problematic and worth changing,
raise it explicitly — never silently deviate.

### Read in-source audit comments at the edit site
[ID: ai-workflow-read-edit-site]

Before the first change to a file, read the code around the target
lines and scan for in-source comments that record prior audits,
experiments, or rejected approaches. Audited code carries comments
stating WHAT WAS TESTED and WHAT THE OUTCOME WAS — written precisely
so the next reader does not re-attempt a known-bad fix. Look for:

- comments dated by session or PR (e.g. "Per-hue audit (S155): ...")
- lists of tested-and-rejected approaches, or "known limitation"
  callouts
- a named regression metric (e.g. "p95 0.024 -> 0.146")

When such a comment bears on the proposed change, the agent MUST
either state its finding and ask whether the change overrides it, or
re-scope from the finding. Reading the comment costs seconds; skipping
it costs multi-session work on an approach the file already records as
broken. This is distinct from matching document convention (that rule
is about form; this is about substance) — a file can match convention
perfectly and still carry a load-bearing audit comment.

When the comment names a rejected mechanism rather than a measured
outcome, the read has a second step: sweep the codebase for that
mechanism per `quality-rejected-mechanism-sweep`. The comment is one
call site's record of a defect that was never filed against the rest.

### Verify working directory before concluding on a negative
[ID: ai-workflow-pwd-on-negative]

Agent shell tools persist the working directory across commands
within a session. An earlier `cd` (yours or implicit from a chained
command) can change where subsequent relative paths resolve, so a
diagnostic that returns empty may be false-negative — running from
the wrong directory rather than the file/entry actually being
missing.

When a path-based shell query (`test -f`, `ls`, `git -C <path>`,
`cat`, etc.) returns empty or fails against a path you have reason
to believe exists, the FIRST diagnostic step MUST be to verify the
working directory (`pwd` or equivalent). Specifically check `pwd`
when:

- `test -f X` returns empty for a file you have grounds to expect
- `git submodule status` returns empty in a repo with known
  submodules — you may be inside a submodule, where the parent's
  submodule list does not apply
- `git ls-tree HEAD <path>` shows no expected entry — you may be
  in a sibling repo or worktree
- Any "from the repo root" diagnostic gives an unexpected negative

During investigative work where the conclusion depends on a
negative result, SHOULD use absolute paths for path-based queries
to remove ambient-directory dependence entirely.

### Survey prior art before inventing domain logic
[ID: ai-workflow-survey-prior-art]

When designing a new rule, scoring formula, aggregation method, or any
domain logic that crosses into territory another field has already
explored, dispatch parallel research agents to canvas what reputable
sources actually do BEFORE writing ADR text or code. First-principles
reasoning produces rules that read defensible but have no external
grounding — and the agent often picks an option with zero prior art
among trusted sources. Findings inform the rule; the absence of prior
art is also data, so document it either way. A five-minute research
dispatch is trivial against shipping a half-fix that needs later
amendment.

### Read the prior spike's close-out before re-investigating
[ID: ai-workflow-prior-spike-closeout]

When a new issue lands in an area a closed spike already explored, read
that spike's closing PR description and final comment trail BEFORE
launching any probe or prototype. A prior spike often already measured
the mechanisms the new issue proposes — rejecting some with data, or
spinning the one viable path into a still-open follow-up — which can
make the new issue a duplicate. Re-running the prior probe only
rediscovers what the close-out already records.

- MUST: before investigating an issue in an area with a closed prior
  spike, read that spike's closing PR plus its last comment trail first.
- SHOULD: link the new issue to the prior spike's findings in its body
  before any code work starts; if those findings already cover it, close
  it as a duplicate instead of re-probing.

This is the internal counterpart to surveying external prior art, and a
sibling of reading in-source audit comments: each keeps the agent from
re-deriving a result the project already paid for.

### Triage prototype cost before building
[ID: ai-workflow-prototype-cost]

Spend prototype budget on the cheapest path to the answer, not the first
path offered.

- **Read the dependency manifest before starting an install time-box.**
  A cheap inspection of `environment.yml` / `requirements.txt` /
  `Cargo.toml` / `go.mod` often shows the budget is already infeasible —
  a pinned old runtime, OS-locked dependencies, or external checkpoint
  downloads — before the timer starts. Reject on cost without the futile
  install attempt.
- **Order multi-option spikes cheapest-first, not in body order.** A
  spike body lists candidates in narrative order, which optimises for
  explaining the problem, not measuring the answer. Re-sort by smallest
  code surface and cleanest probe rationale, and start there. When a
  candidate fails, record its root cause — the next-cheapest candidate
  often shares it and can be rejected on the same probe data without a
  full reprototype. Revert rejected prototypes cleanly to preserve the
  comparison data for the ADR.

### Spike findings home
[ID: ai-workflow-spike-findings]

Interim findings from a multi-AC spike sliced across sessions (a partial
deliverable that does not yet conclude the spike) belong in a comment on
the spike issue — durable, queryable, bidirectionally linked, and
needing no new directory. Do NOT create a `docs/spikes/` directory for
one-off findings: a new directory is itself an architectural decision
that needs its own ADR. The durable artifact is the eventual ADR per the
decision-log rule, citing the interim comment(s).

### Triage by fan-out
[ID: ai-workflow-triage-fanout]

For classification, audit, or triage workloads that apply the same
judgment to N inputs, fan out across agents instead of looping:

- Seed a shared taxonomy by hand-classifying 2–3 representative inputs
  first, so agents don't each invent a slightly different vocabulary.
- Spawn agents in batches (~5), each running the same prompt on one
  input and returning a structured classification (category, severity,
  justification, recommended next step).
- Aggregate the returns into a matrix.
- **Stop fanning out once the taxonomy saturates.** When new runs stop
  producing new categories, the marginal classification adds nothing —
  spend the remaining budget on root-cause analysis and fixes, not on
  running the rest of the population "for completeness."

### Decide before delegating

The agent will build whatever you ask. The expensive mistake is building the
wrong thing fast. Spend time on:
- Which option to pursue (spike first)
- What the acceptance criteria are
- What's in scope and what's not

### Review continuously

Don't queue up 10 tasks and review at the end. Review after each task:
- Preview the result
- Check the diff
- Run the build
- Give feedback immediately — the agent adjusts in real time

### Use feedback loops

When the agent does something wrong, say so explicitly — it corrects
immediately. When it does something right in a non-obvious way, confirm it — the
agent learns what to repeat.

Corrections: "Don't mock the database in tests — we got burned when mocked tests
passed but prod failed."

Confirmations: "Yes, the single bundled PR was the right call here."

### Keep the backlog honest

- Close issues when done — stale open issues confuse future sessions
- Update epic checklists as children complete
- Move items between milestones when priorities shift
- Don't hoard issues — if something won't be done, close it with a reason

---

## Session Structure

A productive session with an AI agent follows this rhythm:

1. **Orient** — "What's the current state? What's next?"
2. **Pick** — choose one task from the backlog
3. **Implement** — agent codes, builds, tests
4. **Review** — human previews, gives feedback
5. **Merge** — commit, PR, merge to main
6. **Repeat or stop** — pick another task or end the session

Keep sessions focused. One theme per session (e.g., "wiki migration" or "lens
detail pages") produces better results than jumping between unrelated topics.

### Invoke skills explicitly

[ID: ai-workflow-explicit-invocation]

When a project has skills or slash commands that also auto-trigger on
natural language, prefer the explicit `/slash-command` form. A natural-
language phrasing can match the wrong skill, and the misfire is silent:
the agent runs a plausible-but-wrong workflow instead of the intended
one. Reserve auto-trigger for the few skills where the intent is
unambiguous.

### Manage the context budget

[ID: ai-workflow-context-budget]

Stay in one session across the revision rounds of a single unit of work.
The research and file context is already loaded, and a fresh session pays
to rebuild it. When context gets tight mid-unit, compact it (e.g.
`/compact focus on <the current artifact and its open feedback>`) rather
than starting over. Start a new session only when switching to a
different unit or phase, per "Keep sessions focused" above.

---

## Lessons Learned

### When to revert vs when to iterate

AI agents make changes cheap, which creates a temptation to keep iterating on a
failing approach. Recognize the difference:

- **Iterate** when the approach is right but the details need adjustment —
  styling tweaks, field mapping errors, off-by-one bugs.
- **Revert** when the approach itself is wrong — the architecture doesn't fit,
  performance got worse, or the complexity isn't justified.
- **Revert and re-scope** when the approach is right and the change is only
  half of the fix — correct on its own terms, and incomplete in a way that
  ships a worse state than shipping nothing.

The signal: if you're on the third round of fixes for the same feature and it
still doesn't feel right, the approach is wrong. Revert cleanly, document why it
failed (in the issue or an ADR), and try a different approach. Don't let sunk
cost drive technical decisions.

A third case sits between the two: a prototype that is **correct but
partial**. It clears the regression bar — the target metric improves and
the control cohort holds — and it is only the first half of a bug with
two mechanisms. Shipping that half leaves the system worse than before,
because the second mechanism nets out the gain: a dropped data track
recovered by the first fix, then mislabelled downstream by the one it
does not address.

The tell is breadth of effect rather than quality of result. The
prototype clears its bar AND exposes a second mechanism it does not
address, or trips tests and effects beyond the target case. That
unexpected breadth is the signal to revert and scope the complete
multi-part fix as one spike — the work is not wrong, the two halves are
simply not independently shippable.

This is distinct from `Middle scope: ship a novel data shape before the
UI`, where each slice stands on its own and the first is useful alone.
Here the first half alone degrades the output, so shipping it buys a
documented half-state and an obligation to finish.

A special case: when a new bug looks like a previously-fixed pattern, the
instinct is to extend the existing fix mechanism. Try it — but measure the
result against a concrete metric, not against "does it look right." If the
metric regresses, revert immediately and document the rejected attempt inline (a
code comment or PR note) so future sessions see the dead end. The
framework-extension attempt is not waste: it falsifies the "same fix applies"
hypothesis cheaply, which is information.

### Verify agent calculations against the system

AI agents can do mental math — and get it wrong. When the agent computes a
score, estimate, or comparison, **always verify against the actual build
output.** The agent may use stale values, wrong field names, or misremember data
from earlier in the conversation.

The build is the source of truth. `npm run build` then check the output. Don't
trust "I calculated 7.9" — check what the page actually renders.

### Verify before relying on a claim

A claim about current state — a count in a memory note, a changelog's list of
breaking changes, the assumption that one fix refreshed every view — is accurate
when written and decays after. Before you scope work or declare a fix shipped on
the strength of such a claim, re-measure the thing itself. The check is usually
one command, and it replaces a guess with proof.

- **Counts in handoff notes decay fast.** A memory note, prior PR body, or
  journal "follow-ups" line that quantifies backlog ("33 stale logs", "5 open
  Dependabot PRs") was true at write time; sweep tasks then complete silently as
  side effects of other work. Re-run the underlying check (`--check`, `gh pr
  list`, `git log --since=`) before estimating effort, and note any large drift
  in the session entry — it is signal about which sweeps are finishing on their
  own. Treat the count as a question, not an answer.
- **A dependency bump is verified by the gate, not the changelog.** Scanning a
  major bump's changelog sizes the question; running the project's
  lint/test/build against the new version answers it. If the local gate passes,
  the bump is safe regardless of changelog content; if it fails, the changelog
  names which breaking change fired. Patch and minor bumps may skip the run when
  the changelog shows no breaking changes.
- **When the truth source changes, audit every downstream render.** When one
  source of truth feeds multiple rendered artifacts (design tokens → CSS +
  Storybook + docs; OpenAPI → SDKs + mocks + docs), updating the source does not
  refresh the renders. Before declaring the fix shipped, list every artifact
  derived from the changed truth and verify each — build-time caches,
  hand-tweaked files, and provenance artifacts that intentionally show the
  pre-fix state each behave differently; call out which.
- **A plan-time placement is a hypothesis, not a fact.** Before writing a rule
  or fix to a planned target file or section, open it and confirm the gap is
  real and the home is semantically correct. Milestone plans routinely
  mis-place: the "missing" rule is already covered two files over, or the
  planned home conflates two concerns (a gate that *verifies* vs a diagnostic
  that *instruments*). The check is one read, and it replaces a guess with the
  file's actual contents.

### Probe before acting on a hypothesis

A bug ticket, a spike, or a prior-session note often arrives with a hypothesized
mechanism, a proposed fix, or an inherited diagnosis. Treat it as a claim to
disprove, not a foundation to build on. Before acting, run the cheapest probe —
a throwaway script, a data dump, a single query — that would confirm or refute
it. One run answers two questions: is the hypothesis correct, and where is the
real signal? The frequent outcome is that the probe inverts the framing and the
real cause sits in a different region than the text predicted.

Run the probe at whichever decision point comes first:

- **Before coding a fix the issue proposes** — when the body names a specific
  code surface and a predicted cause, the fix often belongs somewhere the text
  did not point.
- **Before drafting an ADR** — when the investigation prompts are cheap to
  answer against real data, the measurement frequently flips the recommendation
  an estimate would have reached.
- **At spike intake** — before treating a spike that asserts a specific failure
  ("X happens because Y") as actionable, confirm the assertion against the
  cheapest data dump that would refute it.
- **At the start of a follow-up session** — re-verify any load-bearing diagnosis
  inherited from a prior session's memory; a coarse earlier conclusion may not
  survive a direct probe, and the proposed solution set may be unnecessary.
- **Before filing a bug** — when a short probe (under ~30 min) costs less than
  the next agent's cost to orient, it turns a reproduction-only ticket into a
  root-cause brief with fix options.

Probe the breadth before scoping the fix. When a quality gate flags an issue by
reason code, or two items look like a duplicate, the first probe is how many
items share the symptom — `grep -c <reason_code>` over the gate output, or a
cohort-wide content hash. The breadth changes the category of work: an isolated
1/N case is one fix; a systemic pattern is a different effort and often resolves
to wontdo-and-document an upstream cause (e.g. identical bytes served from
distinct URLs). Designing the fix before measuring breadth risks an
implementation spike on a non-systemic issue, or a small-fix framing on a
cohort-wide one. The probe costs seconds; the misframing costs a wasted spike.
The mechanism generalizes to any cohort with byte-identifiable artifacts —
scraped assets, generated files, captured fixtures, computed reports.

Probe the code surface, not just the data. When the hypothesis is that an
assumption is wired everywhere — "this generalization needs a schema lift,"
"every caller hard-codes the old shape" — the cheapest probe greps the
load-bearing constant or type across the codebase and reads each call site.
The assumption often turns out to be locked in one function while the rest of
the pipeline already iterates polymorphically; sizing that in ten minutes
keeps a one-function change from being scoped as a multi-session rewrite. A
data probe and a code-surface probe answer different questions — one measures
what the bytes are, the other locates where an assumption is encoded — and
both are cheap.

Probe the artifact, not your reading of it. When the claim rests on a dense
source-of-truth artifact — an overlay image, a generated SVG, a log, a chart, a
database row — dump its raw representation (pixel scan, JSON dump, AST walk,
`SELECT`) instead of re-interpreting the rendered view. Repeated reading is
slower and can yield mutually inconsistent conclusions; one raw dump settles the
question.

Prefer the production harness over a throwaway probe when it already emits the
classification. When the question is only "does the failure framing reproduce?"
and the project ships a tool that already produces per-case verdicts — a test
runner, a CI gate, a linter, an auto-triage runner — run that tool first. Its
output is the authoritative classification, not a one-off recomputation; it
needs no script to author or delete; and it re-runs next session without
rebuilding the probe environment. A throwaway probe is justified only when the
production tool cannot answer the question. Signs the harness is the right call:
the issue cites a count from a manual triage you would be recomputing, its
reason codes match the failure classes the issue lists, or its output is
queryable. Thirty seconds of `<tool> --help` is cheaper than writing a probe to
discover the tool already does the job.

Skipping the probe has two visible failure modes: a well-reasoned fix built
against a wrong premise, and a premature ADR that needs same-day supersession.
When the probe inverts the framing, the original text is a useful negative
result — record it in the PR description or the ADR's "approaches ruled out." If
the project exposes no cheap probe for the claim, surfacing that gap is itself
the first output. Probes are throwaway: name them for the issue, delete them
before the commit that uses their findings, and keep the findings in the issue,
ADR, or PR.

### Debugging multi-stage systems

A bug report on a multi-stage system (extract → transform → render →
verify; build pipeline, ETL, compiler, agent-orchestrated workflow)
names a symptom, not a stage — "the output is wrong" says nothing about
where reality first diverged from expectation. Resist probing each stage
in sequence on every report; that scales with stages × reports.

- **Probe the suspected stage directly, not the whole pipeline.** Call
  the stage's helper functions with the smallest input that reproduces
  the bug instead of re-running the production entry point each
  iteration. Direct probes are typically 5–10× faster per iteration and
  surface intermediate state the end-to-end artifact hides. Default to
  end-to-end only when the bug is integration-shaped (works in
  isolation, fails when composed), the stage boundary is unclear from
  the symptom, or fixture setup is expensive.
- **Invest in per-stage diagnostics once the loop repeats.** If you have
  spent more than ~30 min probing the same stage across consecutive
  reports, the next session's deliverable is per-stage diagnostic output
  (a `--debug` dump after each stage), not another probe. Then every
  future report becomes "scan the per-stage artifacts in order, find the
  first divergence" — paid once, saved on every report after.

### Verify external state before a visible action

Some actions land on someone else's surface — filing an issue or opening a PR on
a third-party repo, taking on a dependency, pulling a vendored fixture. Before
one of these, confirm the external state is what you assume. The check is cheap
(a single API call or page load); the cost of skipping it is acting on stale or
wrong information publicly, under the maintainer's identity.

Confirm, before acting:

- **The target is the real project** — search ranking and name collisions lie.
  Verify against the README, the canonical source, or the site the dependency
  claims to be.
- **The repo is live** — not archived, read-only, or migrated. An archived repo
  silently rejects new issues; a moved one routes your action to a dead fork.
- **The channel is open** — issues are enabled, the branch accepts PRs, the
  package version still exists.
- **The terms fit your repo** — an "official" or "recommended" action/tool's
  pricing and license model fits your repo's org type. "Official" is not always
  "drop-in": `gitleaks/gitleaks-action` is free on personal repos but requires a
  paid license secret on organization repos. Verify the pricing model before
  switching, not on the first failing run.

When a check fails, treat it as a signal about your own source of truth, not
just a one-off filing problem. A repo that turns out archived, renamed, or wrong
means the ADR, README, or memory that pointed there is stale — fix the pointer
(or drop the dead trigger) in the same task, rather than working around the
single blocked action.

### Middle scope: ship a novel data shape before the UI

A user-facing feature decomposes into a data layer (types + emit +
tests) and a presentation layer (rendering, accessibility, UX details).
When the data layer is novel — new schema decisions, several viable
shapes — ship it in its own PR before the UI. The first PR gets the
shape reviewed in isolation (required vs optional fields, enum vs
free-form, two- vs three-state); the second focuses entirely on UX
without dragging schema review into it, and without redesign risk if the
first shape turns out wrong.

The same split applies when a feature needs both a schema change and data
ingestion: ship the schema in its own PR with synthetic tests proving the
new code path is reachable, then ship the real data against the
now-stable schema. Schema changes need review for second-order effects
(back-compat, dispatch, coverage); data ingestion needs review for
source-of-truth and format correctness — reviewers focus differently on
each, so combining them in one PR forces a context switch.

Skip this when the data layer is trivial (one field, obvious shape) or
when the UI will inform the data shape — there a vertical slice forces
both decisions together, which is what you want.

### Scope creep within sessions

A productive session can cover a lot of ground. But jumping between unrelated
topics (feature work, data fixes, epic triage, domain decisions) leads to:

- Commits directly to main instead of feature branches
- Incomplete work left uncommitted
- Context switching that reduces quality

**Recommendation:** Commit to a theme per session. When an unrelated topic
surfaces, create an issue and return to it in the next session. If you do switch
topics mid-session, commit and push the current work first.

### Constraints can invalidate a plan mid-execution

When an architectural constraint surfaces mid-execution that makes the agreed
plan unreachable as stated, pause, name the constraint, and re-surface the
option set — each option with its blast radius — for the user to re-decide. Do
NOT scope-creep the fix to absorb the constraint silently: rewriting a fixed
parameter, re-deriving anchor data, or otherwise expanding the blast radius
ships a half-done architectural change. Re-surfacing is cheap; recovering from a
half-done architectural change is not. When the constraint hits, the move is
always stop and re-decide, not plough on.

### Data quality is the real bottleneck

With AI agents, code changes take minutes. But the inputs to those changes —
optical quality scores, prices, field validations — require human judgment and
research. A single lens review can take longer to evaluate than the entire
scoring engine took to build.

Plan for this asymmetry:

- **Code tasks** — delegate freely, review the output
- **Data tasks** — the agent can research and propose, but the human must
  validate against primary sources
- **Judgment calls** — "Is this bokeh score 0.5 or 1.0?" requires domain
  knowledge the agent doesn't have. Expect these decisions to take time. They're
  the most valuable part of the process.

### A local failure CI doesn't reproduce is host maintenance, not a code change

When a local dev or e2e run fails but CI is green on the same revision,
the delta is the environment, not the code. The pull to "fix" it by
changing the app — a production bind, port, or config tweak to satisfy a
local backend quirk — contorts production code for a problem CI already
proves does not exist.

- **Confirm CI parity first.** Same revision green in CI means the code
  is fine; establish that before touching the app.
- **Bisect with a known-good control.** Run a minimal known-working
  container or command (e.g. a stock `nginx`) beside the failing one to
  localize the fault to the specific service versus the whole backend.
- **Verify real capability over startup warnings.** Test the actual
  behaviour (a ping or healthcheck) rather than trusting a scary
  "X not available" log line — such warnings are often benign.
- **Do not modify the app to accommodate a local-only quirk.** Fix the
  environment, switch backends, or rely on CI — and record the finding
  in an issue or the journal instead of changing code.

### Manual workaround for an unmaintained automated path

When a process — human or multi-agent — replicates work that an
automated tool was once meant to do, the highest-leverage move is
usually to investigate the tool, not to scale the manual process. AI
agents amplify this trap because they make manual work feel cheap: a
parallel-agent triage looks like a free lunch until its error rate burns
the savings. Whenever you find yourself architecting a multi-session
manual process for something that "feels like it should be automated
already," check whether an automated path exists and is silently
broken — fixing it is almost always cheaper than scaling the manual one.
The tell: the manual process produces low-quality output (a high
misframe or false-positive rate) AND its outputs are nominally also
produced by a tool somewhere in the stack.
