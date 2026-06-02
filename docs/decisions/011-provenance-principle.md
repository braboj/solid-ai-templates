---
id: "011"
status: Accepted
date: 2026-06-02
category: process
supersedes: []
superseded_by: []
---

# ADR-011: Rules cite their origin incident

## Context

Most "AI coding rules" repositories are speculative — somebody sat
down and imagined what good agent discipline should look like, then
wrote it up. The output reads like a checklist of best-intentions
that may or may not survive contact with a real project.

This project has been different in practice, even before this
principle was named. Looking at the v2.6 cohort (the first
milestone where the pattern was visible):

| Rule | Source incident |
|---|---|
| pwd check before negative conclusion | wuseria session 105 falsely flagged a submodule as missing because the shell `cd`'d into it earlier |
| Probe scripts lifecycle | wuseria PR #988 — 5 iterations of `probe_three_profiles.py` to measure HSV bands, deleted before commit |
| Generated-file banner + `--check` flag | wuseria PR #1013 (and the downstream wuseria ADR for it) — real silent drift between source and committed output |
| Findings docs for empirical thresholds | wuseria's `referenceset/scoring.md`, `calibration.md`, etc. — accumulated reference for empirical numbers |
| Close-and-resubmit when framing drifts | me-fuji session 2026-06-02 — mid-review PR rewrite became unreadable |
| Agent must not produce calibration ground-truth (#381) | wuseria session 111 — agent stopped at scaffolding rather than fake eye-reads |

Every rule has a receipt in another repo's git history. This is
the project's strongest differentiator: not the rules themselves
(any sufficiently disciplined team produces similar lists), but the
fact that each rule was earned by a specific concrete failure.

Without a principle naming this, future contributors may revert
to the imagined-ideal pattern under deadline pressure — adding
rules that "feel right" without grounding them in a witnessed
event. The principle has to be load-bearing to survive.

## Decision

Every new rule added to `templates/` (a new section, a new MUST, a
new SHOULD, a new MAY) SHOULD cite the concrete incident, PR, or
session that surfaced it. The citation lives in the **issue body
that proposes the rule**, not in the template prose itself.

### Rule

When opening an issue that proposes a new template rule, the issue
body SHOULD include:

1. A **Provenance** section near the top (after Context) naming the
   specific incident, PR link, or session marker (date + project)
   where the failure or pattern was observed
2. Enough detail that a reader unfamiliar with the originating
   project can understand what failed and why this rule prevents
   recurrence — a single paragraph is usually enough
3. If the rule generalizes from multiple incidents, list each;
   patterns observed once are weaker evidence than patterns
   observed three times

### Scope

The principle applies to:

- New sections in any `templates/` file
- New imperative bullets (MUST, SHOULD, MAY) inside existing
  sections
- New conventions, workflows, or discipline rules

The principle does NOT apply to:

- Typo fixes, formatting passes, editorial polish
- Refactors that preserve rule semantics
- Smoke checks, test infrastructure, tooling changes (these have
  their own evidence trail in test specs and PR descriptions)
- Documentation updates that summarize existing rules

### Exception: external standards

Rules transcribed from established external standards (OWASP Top 10,
12-factor app, RFC 2119, Semantic Versioning, WCAG, etc.) cite the
standard as the source rather than an originating incident. These
rules codify mature external consensus and the "evidence" is the
standard itself.

### What the citation does NOT have to do

- The template prose itself stays clean — citations live in the
  proposing issue, not in inline comments in template files
- A rule does not need to be re-cited every time it is edited;
  the original proposing issue is the canonical record
- Citations do not need machine-readable structure (no frontmatter
  on rule sections, no schema on the citation form); the issue
  tracker is the receipt store

## Alternatives considered

- **Inline citations in template prose** — rejected; would
  silently bloat templates as rules accumulate, and would rot
  when source projects rename, archive, or go private. Issue
  bodies are append-only history; template prose is live
- **MUST-level enforcement** — rejected for now; some rules
  legitimately come from synthesis across multiple weak signals
  rather than a single load-bearing incident. SHOULD lets
  authors apply judgment while still committing to the discipline
- **Smoke check enforcing citation presence in PR bodies** —
  rejected; out of scope for this ADR (the issue's "Out of scope"
  flagged this explicitly). The mechanism for checking citation
  presence is undefined and would need its own design
- **Retroactive citation audit of existing rules** — rejected;
  out of scope. If the audit surfaces older rules that lack
  origin citations, a separate follow-up issue can decide
  whether to retrofit them or accept that pre-v2.6 rules are
  grandfathered

## Consequences

- The project's README gains a "Forged in real work" framing
  section that turns this principle into the user-facing value
  proposition
- New issue proposals that add template rules without a
  provenance section get pushed back during review (SHOULD-level,
  so judgment applies — but the default expectation is set)
- The contribution shape becomes inductive: contributors are
  expected to bring evidence, not opinions. This raises the bar
  for casual rule additions and discourages speculative "wouldn't
  it be nice if" rules
- The issue tracker becomes a load-bearing artifact — closed
  issues with provenance sections are the project's primary
  evidence base. Issue body content should not be silently
  rewritten after merge
- Adopters gain a way to evaluate rule applicability: if their
  project does not match the originating incident's shape, they
  can deprioritize that rule. Rule-by-rule applicability becomes
  judgable instead of all-or-nothing
- Future maintainers gain a way to deprecate rules: if the
  originating problem is structurally gone (e.g. the tool that
  produced the failure is no longer used), the rule may be a
  candidate for removal

## Related

- `docs/decisions/010-adr-governance.md` defines the frontmatter
  schema this ADR is written under, including the `process`
  category used here
- The v2.6 milestone cohort (issues #342, #347, #358, #360, #364,
  #379, #380, #381, #382) is the empirical evidence base for
  this principle — every issue body in that cohort independently
  cited a real source incident before this ADR was written, which
  is the strongest signal that the principle is descriptive of
  practice and not aspirational
