# Agent Context Trade-offs

How CLAUDE.md size and the mandatory startup block affect agent
latency and quality, and how to reason about the trade-off.

This document is descriptive — it characterizes the trade-off so
project maintainers can make informed decisions. Specific timing
figures are illustrative, not measured for this repo. Where a number
appears with a range (e.g. "~3–8s"), treat it as order-of-magnitude
intuition, not a benchmark.

---

## TL;DR

- **Cold-start cost** = full prompt processed from scratch (templates
  + CLAUDE.md + memory). This is where bloat hurts.
- **Within-session cost** ≈ 0 once cached (Anthropic prompt cache TTL
  is ~5 minutes).
- **Bigger context dilutes attention**; smaller context increases the
  risk that a rule isn't visible when needed.
- **Optimize for clarity, not bytes.** A 15 KB document where each
  rule is one line beats a 30 KB document where the same rules are
  scattered through changelogs.

---

## Latency

Three distinct costs, each driven by different mechanics.

### First-token latency

Time from user pressing Enter to the first character of the response.
Driven primarily by *uncached* prompt processing.

With prompt caching enabled (the default for Claude), a stable prompt
prefix is cached for ~5 minutes. Adding 100 KB to a cached prompt
adds milliseconds, not seconds. The cache is keyed on prompt prefix
— anything that changes the prefix (a settings reload, an edited
CLAUDE.md, a hook injecting different text per turn) invalidates the
cache and forces a cold prefill.

### Tool round-trip overhead

Each tool call is a separate model invocation. A turn that does 17
Reads upfront pays a setup cost per Read (network round-trip, harness
scheduling, model decision to call the next tool).

This is bounded — typically ~1–3s total for 17 sequential Reads. It
matters most on the first turn of a session, when a mandatory-startup
block forces a fan of Reads before the agent can respond.

### Cold-start cost

The first message in a new conversation. Nothing is cached. The full
prompt processes from scratch.

This is where bloat hurts. A 28k-token system prompt cold-starts
noticeably slower than a 10k-token one (illustrative: ~3–8s vs ~1–2s
before the model begins generating). Within the session the cache
holds and CLAUDE.md size barely matters — but every new session pays
the cold cost again.

---

## Quality

Three distinct effects, none of them strictly proportional to byte count.

### Convention compliance

Rules the model sees on every turn get applied reliably. Rules behind
a "read on demand" trigger only apply if the trigger fires.

This is the biggest argument *against* moving rules out of CLAUDE.md
when the agent needs them every turn. If a rule's failure mode is
silent (the agent quietly does the wrong thing rather than erroring),
"agent will read it when needed" is a weaker guarantee than "agent
sees it every turn." The mandatory startup block exists for exactly
this reason: it forces the agent to load binding rules before the
first response, when a forgotten rule would do the most damage.

### Context window pressure

A bigger system prompt leaves less room for tool results, files, and
conversation history. Matters on long sessions approaching the context
limit; irrelevant on short ones.

A typical context budget calculation: a 200k-token window with a 28k
system prompt leaves ~172k for everything else. Most sessions never
fill that — but a session that reads many large files or runs many
tool calls can.

A startup block that force-reads N templates contributes to context
pressure on top of CLAUDE.md itself. Rough budget intuition: 17 base
templates run ≈ 80–120 KB ≈ 20–30k tokens — about 2–3% of a 1M-token
window, or 10–15% of a 200k window. Comfortably within budget on
modern windows. The point isn't that template loading is free — it's
that *fit* is rarely the failure mode. The failure modes that matter
are convention compliance and attention dilution.

### Attention dilution

Models pay less attention to rules buried in long context than to
rules in a short, focused document. Counterintuitive but real: a 30
KB CLAUDE.md with rules scattered through changelogs, package
architecture notes, and per-feature progress logs is *less reliably
applied* than the same rules in a 15 KB document where every line is
a rule.

This is the strongest argument for content discipline. The aim is not
to make CLAUDE.md small for speed — it is to make every line a rule
the model can see clearly. Changelogs, package architecture, and
per-feature progress dilute attention without adding to compliance.

Loading many templates is usually fine on this axis — structured
separation helps the model keep topics distinct, and the imperative
tone of well-written templates is easier to track than mixed prose.
The patterns that break this (redundant rules across templates,
loaded-but-irrelevant templates) and what they imply for code review
and audits are covered in detail in
`docs/meta/template-content-quality.md` — that's the operational
home for keeping the template library in shape so this section's
"mostly fine" stays true.

---

## Implications for templates

### Why the mandatory startup block exists

The startup block (project's CLAUDE.md instructing the agent to read
all referenced template files before its first response) is a
**deliberate trade-off**: a one-time per-conversation cost (~5s once,
cached after) in exchange for reliable convention compliance on every
turn of the session.

Without the block, the agent reads templates *on demand* — which
works fine until a turn that should have consulted a template doesn't,
because the agent didn't realize it was relevant. The block trades
some cold-start latency for predictable rule application.

For projects where the user values speed over compliance, the block
can be omitted and templates can be referenced from CLAUDE.md instead.
For projects where rules are load-bearing (security, data integrity,
release process), the block is recommended.

### When to trim CLAUDE.md

Trim CLAUDE.md when:

- A rule has migrated to a code-side home (lint config, type system,
  test fixture) — leave a one-line pointer if discoverability matters,
  otherwise delete
- A "rule" is actually a changelog entry, a package architecture
  description, or per-feature progress — these belong in ADRs, the
  README, or `docs/dev-journal.md`
- A paragraph-length rule is really a decision with context — split
  into an ADR and a one-line pointer here
- Multiple rules say the same thing in different sections —
  consolidate to a single home

The wrap-up doc-placement decision tree (see
`templates/base/workflow/ai-workflow.md` Doc placement decision tree
section) is the operational gate.

### When NOT to trim

Do not trim CLAUDE.md when:

- The rule must fire on every turn and has no code-side enforcement
  (e.g. "always commit on a branch, never on main")
- The rule is short, imperative, and the file isn't dilution-heavy yet
- Removing the rule would push the agent to "ask the user" repeatedly
  for something the user has already decided once
- The size is from rules (compliance-driving) rather than narrative
  (dilution-driving)

### Trade-off framing for project maintainers

When the question is "should this go in CLAUDE.md?", reframe as:

1. **Is this a rule the agent must apply on every turn?** If no, it
   doesn't belong in CLAUDE.md — see the doc-placement decision tree.
2. **If yes, can the rule be one line?** If yes, add it. If no, write
   an ADR and leave a one-line pointer.
3. **Does CLAUDE.md already say this?** If yes, consolidate.
4. **Does an existing rule cover this generally?** If yes, leave the
   general rule; resist adding specific cases.

The result is a CLAUDE.md where every line earns its place by being a
rule the agent will apply on the next turn.

---

## Source material

This document originated as a conversation between a project
maintainer and Claude Code during a wuseria session investigating why
the project's CLAUDE.md (29 KB / 349 lines) had started feeling slow.
The audit identified the mandatory startup block + a single 4,361-
character bullet under §1.2 as the latency contributors, and the
attention-dilution effect as the underlying quality problem.

The specific figures here (cold-start times, cache TTL, token counts)
are drawn from that conversation's domain reasoning, not from
controlled measurement on this repo. They should be treated as
intuition for reasoning about the trade-off, and refined with real
measurement when the question gets quantitative.

Related work:

- `templates/base/workflow/ai-workflow.md` Doc placement decision tree
  — the routing logic this document references
- `templates/base/workflow/scope.md` end-of-session step 6 — the
  operational gate that applies the decision tree
- Issues #354 and #355 — the rules above were codified in those PRs
