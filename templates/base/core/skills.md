# Skill Authoring
[ID: base-skills]

Structure, triggering, and quality rules for authoring agent skills —
`.claude/skills/<name>/SKILL.md` files with YAML frontmatter and a body
of on-demand instructions. Companion to the context-file spec in
`templates/base/core/agents.md`: that governs always-loaded rules, this
governs on-demand procedures.

---

## When to write a skill
[ID: skills-when]

A skill is a procedure or judgment the agent loads only when a task
matches its description. It is not always-loaded context. Write one only
when all three hold:

- **Too big for every-turn context** — inlining the procedure in
  `CLAUDE.md` or a template would dilute rules the agent needs on every
  turn (see `docs/meta/agent-context-tradeoffs.md`)
- **Not needed every turn** — it applies only when a recognizable task
  arrives (write a post, score an article, deploy), not continuously
- **Reusable** — the same procedure recurs across sessions; a one-off
  belongs in the conversation, not a skill

A rule that MUST fire on every turn belongs in `CLAUDE.md` or a template,
never a skill — a skill the agent forgets to invoke is weaker than an
always-loaded rule. Do NOT create a skill that restates always-loaded
context: it is redundant and drifts from its source (see the single
source of truth rule in `templates/base/core/agents.md`).

---

## Frontmatter
[ID: skills-frontmatter]

- `name` and `description` are the only required keys. Add another key
  only for a real behavior, not for metadata the runtime ignores
- `name` MUST be kebab-case and match the skill's directory name
- `disable-model-invocation: true` marks a skill as explicit-invocation
  only (`/name`); omit it for skills that should auto-trigger
- A long `description` uses a YAML block scalar (`>-`) so it wraps
  without embedded newlines

---

## Writing the description
[ID: skills-description]

The `description` is the highest-leverage line in the file: it is the
only text the model matches against to decide whether to trigger. Write
it for retrieval, not for humans.

- Open with an imperative purpose clause, then "Use when …", then the
  concrete trigger phrases a user would actually type. The model matches
  on those phrases, so name them literally
- Write in the third person about the user's request ("Use when the user
  asks to …"), not second person to the model
- State what the skill is NOT for when a near neighbor would otherwise
  mis-trigger it
- For an explicit-only skill, put the invocation in the description
  ("Invoke with `/name <arg>`") alongside `disable-model-invocation`
- Name a relationship to another skill when one invokes the other, so
  the skill graph is discoverable

---

## Body structure
[ID: skills-structure]

Order: purpose → workflow index → steps → output format → constraints.

- Open with an H1 title and a one-sentence restatement of purpose
- Follow with a numbered `## Workflow` that lists the steps in order and
  doubles as a map to the detailed sections below
- Give each step a numbered, imperative heading ("## Step 1: Read the
  target")
- Ship the exact output or report format inline as a skeleton the model
  fills, not a prose description of it
- End with a `## Constraints` section for hard rules and don'ts
- State a core principle or calibration note when the skill applies
  mechanical rules, so they are not over-applied ("signals, not proof")

Annotated skeleton:

```markdown
---
name: skill-name
description: >-
  <Imperative purpose>. Use when the user asks to <task> —
  "<trigger phrase>", "<trigger phrase>", "<trigger phrase>". Not for
  <near neighbor to exclude>.
---

# Skill Name

<One sentence restating what this skill does.>

## Workflow

1. <Step one, imperative>
2. <Step two>
3. <Step three>

## Step 1: <imperative heading>

<What to do. Point to reference.md or scripts/ where detail lives.>

## Output

<Fenced or ###-structured skeleton the model fills in.>

## Constraints

- <Hard rule>
- <Don't>
```

---

## Progressive disclosure
[ID: skills-disclosure]

- Keep `SKILL.md` to procedure and judgment. Move exhaustive catalogs,
  lookup tables, and long references to a sibling `reference.md` (or
  `references/*.md`) and point to it by name at the step that needs it
- Tell the model the reference is authoritative and any inline list is a
  subset ("the high-frequency ones; full catalogue in `reference.md`")
- Share one reference across skills rather than copying it — a duplicated
  catalog drifts, the same single-source-of-truth rule that governs
  context files

---

## Bundled scripts
[ID: skills-scripts]

- Bundle a deterministic mechanical pass as `scripts/scan.sh` for
  anything a regex can catch, so it does not burn model attention.
  Invoke it with an explicit relative path in a fenced block
- Split script output into a violations bucket (every hit is a finding)
  and a review bucket (over-flagged by design, judge in context) and
  tell the model which is which
- State the script's limits so it is not over-trusted ("a clean scan is
  not a passing score; the scanner catches only what a regex reaches").
  A stated check names the command that runs it and the condition that
  passes it, beside the rule it enforces
- Wrap existing project tooling by path (an npm script, a Python tool)
  rather than re-implementing its logic in the skill

---

## Length and tone
[ID: skills-length]

- Right-size to the task: roughly 50–90 lines for a mechanical,
  single-purpose skill; 130–220 for a judgment-heavy one. Past ~220,
  split detail into a reference
- Write imperatively to the agent ("Read the full input", "Do not skip
  the review step"). Use directive absolutes for critical ordering
- Encode specific, hard-won lessons with concrete example cases, not
  generic advice — a named past failure teaches more than an abstraction
- Keep the prose de-slopped; a skill that produces prose should run its
  own output through the project's writing check before shipping

---

## Self-check
[ID: skills-self-check]

Run against a drafted skill before delivering it. Every item must hold;
a failing item is a fix, not a note:

- Does this need to be a skill, or does it belong in always-loaded
  context because it must fire every turn?
- Does the description name the literal phrases a user would type to
  trigger it?
- Is any exhaustive catalog inlined that should be a shared `reference.md`?
- Does the body restate a rule that is authoritative in another skill,
  a template, or `CLAUDE.md`?
- Does every mechanically checkable step name its check?
- Is the output format shipped as an inline skeleton, not described in
  prose?
