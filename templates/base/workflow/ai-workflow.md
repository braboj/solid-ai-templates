# AI-Assisted Development Workflow
[ID: base-ai-workflow]

How to structure work when collaborating with AI coding agents. Covers the project lifecycle, work item hierarchy, and practices that maximize agent effectiveness.

## Lifecycle Phases

### 1. Spike (Explore)

Conversational research to understand the problem space and generate recommendations.

**What the human does:**
- Defines the question or area to explore
- Validates findings against domain knowledge
- Decides whether to proceed

**What the agent does:**
- Researches codebases, documentation, and web sources
- Compares alternatives with tradeoffs
- Produces a recommendation with rationale

**Output:** A decision or ADR (Architecture Decision Record) documenting the choice and why.

**Anti-pattern:** Skipping the spike and jumping to code. The agent will build whatever you ask — the question is whether it's the right thing to build.

### 2. Prototype

A throwaway implementation to validate feasibility and UX direction.

**What changes with AI:**
- Prototypes are nearly free — an agent can build one in a single session
- The bottleneck shifts from building to deciding. Have the conversation about what you want before generating code
- Prototype code should be disposable. Don't polish it — test the concept, then rebuild properly

**Output:** A working demo the stakeholder can interact with. Keep or discard based on feedback.

**Anti-pattern:** Polishing the prototype into the product. Prototype code carries technical debt from speed-first decisions.

### 3. Design

Define the MVP scope, data model, architecture, and conventions.

**What to produce:**
- Architecture Decision Records for non-obvious choices
- Data model (types/interfaces)
- Page/component structure
- Convention file (CLAUDE.md or equivalent) so the agent follows project rules across sessions

**Key principle:** The convention file is the agent's long-term memory. Anything not written down will be forgotten between sessions. Invest time in CLAUDE.md — it pays back on every future conversation.

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

**Agent role:** Write the workflow files, configure build steps, troubleshoot deployment failures.

**Human role:** DNS, domain registration, secrets, access tokens — things that require account access.

### 6. Monitor

Track errors, performance, and user feedback.

**Agent role:** Set up monitoring config, analyze logs, investigate reported issues.

**Human role:** Watch dashboards, collect user feedback, prioritize fixes.

---

## Work Item Hierarchy

### Epic

A large initiative spanning multiple sessions. Too big for one task.

**Good epic:** "Genre Scoring System" — clear goal, multiple components, measurable completion.

**Bad epic:** "Make the site better" — no clear scope or completion criteria.

**Rules:**
- Every epic needs a checklist of child issues
- Track completion by checking off children as they close
- Epics span phases — don't force them into one milestone
- Close the epic when the goal is met, even if stretch items remain

### User Story

Describes a capability from the user's perspective. Guides the agent toward the right outcome.

**Format:** "As a [user type], I want [capability] so that [benefit]."

**Examples:**
- "As a budget photographer, I want to sort lenses by optical quality and price so that I can find the best value."
- "As a nightscape shooter, I want to filter lenses by coma score so that I only see lenses suitable for astrophotography."

**Why stories matter for AI agents:** Agents take instructions literally. A user story gives the agent the user's perspective, not just a technical specification. This produces better UX decisions when the agent has latitude.

### Task

An atomic, implementable unit of work. One task = one branch = one PR.

**Good task:** "Add OQ column to Lens Explorer table and mobile cards, computed from weighted optical field average."

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

**Why context matters for AI agents:** "The page broke" forces the agent to guess. "The wiki filter shows 0 entries on preview after the Content Collections migration" lets the agent diagnose immediately.

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

### Decide before delegating

The agent will build whatever you ask. The expensive mistake is building the wrong thing fast. Spend time on:
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

When the agent does something wrong, say so explicitly — it corrects immediately. When it does something right in a non-obvious way, confirm it — the agent learns what to repeat.

Corrections: "Don't mock the database in tests — we got burned when mocked tests passed but prod failed."

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

Keep sessions focused. One theme per session (e.g., "wiki migration" or "lens detail pages") produces better results than jumping between unrelated topics.

---

## Lessons Learned

### When to revert vs when to iterate

AI agents make changes cheap, which creates a temptation to keep iterating on a failing approach. Recognize the difference:

- **Iterate** when the approach is right but the details need adjustment — styling tweaks, field mapping errors, off-by-one bugs.
- **Revert** when the approach itself is wrong — the architecture doesn't fit, performance got worse, or the complexity isn't justified.

The signal: if you're on the third round of fixes for the same feature and it still doesn't feel right, the approach is wrong. Revert cleanly, document why it failed (in the issue or an ADR), and try a different approach. Don't let sunk cost drive technical decisions.

### Verify agent calculations against the system

AI agents can do mental math — and get it wrong. When the agent computes a score, estimate, or comparison, **always verify against the actual build output.** The agent may use stale values, wrong field names, or misremember data from earlier in the conversation.

The build is the source of truth. `npm run build` then check the output. Don't trust "I calculated 7.9" — check what the page actually renders.

### Scope creep within sessions

A productive session can cover a lot of ground. But jumping between unrelated topics (feature work, data fixes, epic triage, domain decisions) leads to:

- Commits directly to main instead of feature branches
- Incomplete work left uncommitted
- Context switching that reduces quality

**Recommendation:** Commit to a theme per session. When an unrelated topic surfaces, create an issue and return to it in the next session. If you do switch topics mid-session, commit and push the current work first.

### Data quality is the real bottleneck

With AI agents, code changes take minutes. But the inputs to those changes — optical quality scores, prices, field validations — require human judgment and research. A single lens review can take longer to evaluate than the entire scoring engine took to build.

Plan for this asymmetry:

- **Code tasks** — delegate freely, review the output
- **Data tasks** — the agent can research and propose, but the human must validate against primary sources
- **Judgment calls** — "Is this bokeh score 0.5 or 1.0?" requires domain knowledge the agent doesn't have. Expect these decisions to take time. They're the most valuable part of the process.
