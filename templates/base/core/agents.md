# Output Format
[ID: base-agents]

Structure, models, and formatting rules for generating project
context files.

---

## Output files

| File | Read by | When to use |
|------|---------|-------------|
| `CLAUDE.md` | Claude Code | Claude Code is the primary agent |
| `AGENTS.md` | Codex CLI, Devin, Cursor, Windsurf, Claude Code (fallback) | Cross-agent compatibility |

Both files use the same structure. Generate `CLAUDE.md` for Claude
Code projects, `AGENTS.md` for everything else, or both for maximum
coverage. A single `AGENTS.md` is sufficient if no Claude-specific
rules are required.

---

## Choosing a model

| | Inline | Hybrid | Reference |
|---|---|---|---|
| **Runtime** | Rules always in context | Critical rules in context; agent must read the rest | Agent must read all template files first |
| **Reliability** | Highest — nothing to skip | High — key rules survive even if agent skips references | Lowest — agent may skip referenced files |
| **Maintenance** | Rules drift from templates | Project-specific rules drift; base rules stay in sync | Single source of truth |
| **Best for** | Single project | Multi-project with high-stakes rules | Multi-project, disciplined agents |

**Recommendation:** default to hybrid for the best trade-off. Use
inline when the project does not vendor the templates. Use reference
only when all agents reliably follow startup instructions.

### Why not pure reference?

There is no guarantee an agent will read referenced files. Agents may
skip them due to context limits, instruction-following gaps, or tool
errors. Any rule that causes significant damage when missed MUST be
inlined — do not rely on references alone for critical conventions.

---

## Quality bar

What separates a context file that works from one that dilutes itself.
These apply to all three models; the review process checks them.

### Principles

- **Signal density over length.** Every line is a rule the agent
  applies on the next turn — no changelogs, architecture notes, or
  progress logs. Keep the qualifier or scope a rule needs to be
  followed; never compress away a load-bearing clause. Optimize for
  clarity, not bytes (see `docs/meta/agent-context-tradeoffs.md` and
  `templates/base/workflow/compression.md`).
- **One line per rule.** A rule that needs a paragraph is a decision
  with context — write an ADR and leave a one-line pointer (see the
  Doc placement decision tree in
  `templates/base/workflow/ai-workflow.md`).
- **Single source of truth.** Never restate a rule that is
  authoritative in a skill, ADR, README, or template — point to it.
  Duplicated rules drift, and the agent gets no signal which copy
  wins (see `templates/base/core/docs.md`).
- **State precedence when authorities compete.** When a project has
  more than one rule source (ADRs, skills, vendored templates), state
  the override order near the top: who wins when they differ.
- **Inline load-bearing rules, reference the rest.** A rule whose
  violation is silent or expensive (safety, git, project landmines)
  MUST be inlined; the full framework is referenced (see "What to
  inline", above).
- **Pair a checkable rule with its check.** A mechanically checkable
  constraint names its agent-runnable check — command plus pass
  condition; subjective rules stay declarative (see
  `quality-gates-pair-check` in
  `templates/base/workflow/quality-gates.md`).

### Self-check

Run against a drafted file before delivering it. Every item must
hold; a failing item is a fix, not a note:

- Every line states a rule the agent applies next turn — no changelog,
  architecture, or progress narrative.
- No rule is a paragraph that should be an ADR plus a one-line pointer.
- No prose restates a rule that is authoritative elsewhere (skill,
  ADR, README, template).
- If more than one authority governs the project, the precedence order
  is stated.
- Every mechanically checkable constraint names its check.
- The Project structure section points to the README map, not a
  duplicated directory tree (ADR-020).

---

## Inline model

All rules are inlined — the output file is self-contained. Use numbered
headings for groups and subsections to enable cross-referencing between
documents (e.g. "see CLAUDE.md section 2.3").

Add `Model: inline` to section 1.1 so agents know the file is
self-contained and no external templates need to be read.

Separate project rules (1–4) from agent instructions (5). Project rules
describe *what the rules are*. The review process describes *how to check
them*.

```
# [Project Name]

[One-sentence description from interview]
[IDENTITY answers: owner, repo URL, live URL if applicable]
- Model: inline

## 1. Project
### 1.1 Overview
[Stack template — Stack section]
### 1.2 Project structure
[Pointer to README "Project structure" + agent-specific placement
rules — never a second directory tree (see docs.md, single source
of truth)]
### 1.3 Commands
[Stack template — Commands section]

## 2. Code conventions
### 2.1 Git
[templates/base/core/git.md + any stack EXTEND/OVERRIDE]
### 2.2 [Language]
[Language-specific conventions from stack template]
### 2.3 [Additional code sections as needed]
[Components, styling, data rules — project-specific]

## 3. Quality
### 3.1 Testing
[Stack template — Testing section]
### 3.2 [Additional quality sections as needed]
[SEO, performance, accessibility — project-specific]

## 4. Identity
### 4.1 Design
[Interview DESIGN answers, if applicable]
### 4.2 Brand voice
[Interview BRAND answers, if applicable]

## 5. Review process
### 5.1 Code review
[templates/base/core/review.md priority order + checklists to apply]
### 5.2 Structure audit
[Which templates to verify, when to run]

## 6. Session protocol
Follow `templates/base/workflow/scope.md` for scope guard and end-of-session audit.
### 6.1 Start of session
[templates/base/workflow/scope.md — Session startup + Mandatory startup block]
### 6.2 During the session
[templates/base/workflow/scope.md — During work]
### 6.3 End of session
[templates/base/workflow/scope.md — End of session audit. Render this
ONE of two ways: inline the full checklist VERBATIM, or hard-delegate
with an imperative — "Read scope.md (End of session audit) and execute
each item sequentially; do not summarize or skip." NEVER paraphrase the
checklist into a short bullet list: that silently drops steps and the
"print and execute sequentially" enforcement, producing a thin wrap-up.]
```

Top-level sections 1–6 are role-fixed (§4 is always Identity, §5 is
always Review) — never renumber and never omit them. A top-level
section that does not apply keeps its numbered heading with a one-line
`Not applicable — <reason>` body (e.g. §4 Identity for a backend
service). Omit only non-applicable subsections (e.g. 3.2+ if only
testing applies). This applies to all three models.

---

## Reference model

Use only when all agents reliably follow startup instructions. The
agent file is leaner — it references the templates for base rules and
only inlines project-specific overrides. Same grouped structure and
numbering as the inline model.

Add `Model: reference` to section 1.1 so agents know to read the
referenced templates before starting work.

```
# [Project Name]

[One-sentence description from interview]
[Link to architecture docs if applicable]

Quality conventions defined in `docs/solid-ai-templates/` (submodule).
Key references:
- [List the relevant base and layer templates for this stack]

Project-specific overrides and additions follow below.

## 1. Project
### 1.1 Overview
[Stack template — Stack section]
### 1.2 Project structure
[Pointer to README "Project structure" + agent-specific placement
rules — never a second directory tree (see docs.md, single source
of truth)]
### 1.3 Commands
[Stack template — Commands section]

## 2. Code conventions
[PROJECT-SPECIFIC SECTIONS ONLY — e.g. Type design, Data rules,
Component conventions. Omit anything already covered by the
referenced templates.]

## 3. Quality
[PROJECT-SPECIFIC SECTIONS ONLY — e.g. SEO, Performance targets.
Omit anything already covered by the referenced templates.]

## 4. Identity
### 4.1 Design
[Interview DESIGN answers, if applicable]
### 4.2 Brand voice
[Interview BRAND answers, if applicable]

## 5. Review process
### 5.1 Code review
Follow templates/base/core/review.md priority order, apply templates/base/core/quality.md and
language-specific templates as the standard.
### 5.2 Structure audit
Verify MUSTs from templates/base/core/docs.md, templates/base/core/readme.md, templates/base/core/git.md, and
relevant layer/stack templates. Run after: new project, migration,
new layer, or pre-release.

## 6. Session protocol
Follow `templates/base/workflow/scope.md` for scope guard and end-of-session audit.
### 6.1 Start of session
[templates/base/workflow/scope.md — Session startup + Mandatory startup block]
### 6.2 During the session
[templates/base/workflow/scope.md — During work]
### 6.3 End of session
[templates/base/workflow/scope.md — End of session audit. Render this
ONE of two ways: inline the full checklist VERBATIM, or hard-delegate
with an imperative — "Read scope.md (End of session audit) and execute
each item sequentially; do not summarize or skip." NEVER paraphrase the
checklist into a short bullet list: that silently drops steps and the
"print and execute sequentially" enforcement, producing a thin wrap-up.]
```

---

## Hybrid model

Inline the rules that cause the most damage when missed. Reference the
templates for the full quality framework. The agent file is shorter
than inline but safer than pure reference.

### What to inline

- **Git conventions** — wrong branch names or commit formats pollute
  history and are hard to fix retroactively
- **Project structure placement rules** — wrong file placement breaks
  builds and confuses navigation; the directory map itself stays in
  README (see docs.md, single source of truth)
- **Language-specific safety rules** — e.g. no `set:html`, no `any`,
  no raw SQL — violations introduce security or correctness bugs
- **Content rules** — formatting, writing style, and structure that
  define the project's voice (if applicable)
- **Session protocol / end-of-session audit** — a procedural checklist
  is skipped silently when condensed; it belongs in the active tier,
  not "reference the rest" (see §6.3)

### What to reference

- Quality framework (architecture, readability, maintainability)
- Review process and priority order
- Testing conventions and coverage thresholds
- Documentation standards and ADR format
- Accessibility and SEO rules
- Deployment, CI/CD, and release process

### Identity field

Add `Model: hybrid` to section 1.1 so agents know to read the
referenced templates before starting work.

### Structure

```
# [Project Name]

[One-sentence description from interview]

Quality conventions defined in `docs/solid-ai-templates/` (submodule).
Key references:
- [List ALL base, layer, and stack templates in the dependency chain]

Project-specific overrides and additions follow below.

## 1. Project
### 1.1 Identity
- Model: hybrid
[IDENTITY answers: owner, repo URL, stack, hosting]
### 1.2 Project structure
[Pointer to README "Project structure" + agent-specific placement
rules — never a second directory tree (see docs.md, single source
of truth)]
### 1.3 Commands
[Stack template — Commands section]

## 2. Code conventions
### 2.1 Git
[INLINED — templates/base/core/git.md + project-specific overrides]
### 2.2 [Language]
[INLINED — safety rules, naming, strictness]
### 2.3 [Additional project-specific sections]
[INLINED — content rules, data rules, component conventions]

## 3. Quality
[Reference templates for testing, SEO, accessibility, performance.
Inline only project-specific targets or deviations.]

## 4. Identity
### 4.1 Design
[Interview DESIGN answers, if applicable]
### 4.2 Brand voice
[Interview BRAND answers, if applicable]

## 5. Review process
Follow templates/base/core/review.md priority order, apply templates/base/core/quality.md and
language-specific templates as the standard.

## 6. Session protocol
Follow `templates/base/workflow/scope.md` for scope guard and end-of-session audit.
### 6.1 Start of session
[templates/base/workflow/scope.md — Session startup + Mandatory startup block]
### 6.2 During the session
[templates/base/workflow/scope.md — During work]
### 6.3 End of session
[templates/base/workflow/scope.md — End of session audit. Render this
ONE of two ways: inline the full checklist VERBATIM, or hard-delegate
with an imperative — "Read scope.md (End of session audit) and execute
each item sequentially; do not summarize or skip." NEVER paraphrase the
checklist into a short bullet list: that silently drops steps and the
"print and execute sequentially" enforcement, producing a thin wrap-up.]
```

---

## Vendoring the templates

The reference and hybrid models both vendor this repository as a
submodule. That puts files on disk which the consuming repository does
not track, and any tool that walks the tree rather than the VCS index
will scan them — linters, formatters, secret scanners, spell checkers,
link checkers.

- MUST exclude the submodule path in each such tool's config before the
  first commit. Tools scoped by an explicit file list need no change
- CI may not reveal the problem: checkout actions commonly skip
  submodules by default, so the CI job sees an empty directory while the
  local command contributors are told to run before pushing fails. A
  green dashboard is not evidence here

A consuming repository asks two different questions of the upstream
templates, and they need different revisions. The two coincide only
when the pin equals HEAD.

- "Has this already been raised?" MUST be answered against the upstream
  issue list at HEAD. Reading the pinned file answers "does this rule
  exist in the revision we pin", which is a different question, and
  produces duplicate issues against rules already fixed upstream —
  inside the commits the pin is behind
- "What do our rules require?" MUST be answered at the pinned revision:
  `git -C <submodule> show HEAD:templates/<file>`. This is the more
  damaging direction to get wrong, because it yields a citation rather
  than a duplicate: a rule read from HEAD and quoted as governing does
  not govern until the pin moves, and it makes a local document look
  conformant when it is not
- Never read from `origin/main`, and never from the working tree after
  a bare `fetch`. Fetching makes `origin/main` live while the pin stays
  put, so anything read there describes a future state of the consuming
  repository, not its current one

---

## Monorepo support (optional)

Some agents walk the directory tree from the project root to the
current working directory, reading context files at each level.
For monorepos, add package-level files with package-specific rules:

```
AGENTS.md              # root — shared conventions
packages/
  api/
    AGENTS.md          # API-specific rules (extends root)
  web/
    AGENTS.md          # frontend-specific rules (extends root)
```

Package-level files SHOULD only contain rules that differ from or
extend the root.

---

## Companion documents

All three models MUST also generate:
- `docs/ONBOARDING.md` — following the structure in
  `templates/base/core/docs.md`
- `docs/PLAYBOOK.md` — following the structure in `templates/base/core/docs.md`
- `docs/dev-journal.md` — following the structure in
  `templates/base/core/docs.md`

---

## Shared formatting rules

- Use fenced code blocks with a language tag for all commands and code samples
- Use bullet lists for rules; avoid prose paragraphs inside rule sections
- Keep lines under 80 characters where possible
- No HTML — Markdown only

---

## Shared tone

- Imperative and direct: "Use X", "Never do Y", "Always Z"
- No explanatory prose unless a rule needs context to be followed correctly
- Rules are instructions to the agent, not documentation for humans
