---
id: "036"
status: Accepted
date: 2026-09-01
category: tooling
supersedes: []
superseded_by: []
---

# ADR-036: Chain size is capped by a frozen ceiling, not merely reported

## Context

The template corpus doubled between `v2.1.0` and `v2.72.0` — 387,186 bytes
to 782,467, and 359 RFC 2119 occurrences to 858 — while the file count
stayed flat at roughly 75. The growth therefore landed inside the files
every chain already carries. Five of them — `core/quality.md`,
`core/git.md`, `core/docs.md`, `core/testing.md` and
`workflow/quality-gates.md` — hold 82% of the smallest resolved chain, and
all five resolve into 17 of 17 stack chains.

What a consumer downloads has grown with it. The smallest chain,
`stack-python-lib`, resolves to 370,154 characters, roughly 92,500 tokens
before the project's own context file is read. The largest, `stack-django`,
is 453,564.

`tools/sync.py` already measures every chain to generate the README's
model-limitations table, and `--check` fails when the table drifts from the
tree. That machinery makes the number accurate. Nothing makes it binding: a
rule added to a seventeen-chain file updates the table and passes every
gate, so the cost of an addition is visible only to a reader who goes
looking for it.

A grooming pass on 2026-09-01 read every backlog ticket proposing a
core-tier rule. Each carried observed harm, most measured their own reach,
and several carried data from consuming repositories. There is no
population of low-value tickets to reject. Every addition is justified on
its own terms and the cost appears only in aggregate — which is the trade
no single ticket review is positioned to make.

## Decision

1. **Every root carries a ceiling** — `tests/chain-budget.txt` records one
   ceiling per root a project can pick: every stack, and every orthogonal
   template opted into independently of the stack. A root without a ceiling
   MUST fail rather than resolve unmeasured.

2. **A chain over its ceiling fails the suite** — the check runs in the
   smoke suite, which CI executes on every pull request. The failure MUST
   name the chain, the overage, and the file to edit.

3. **The ceiling is frozen at the measured size** — it MUST NOT carry a
   percentage band or headroom. Shrinking passes freely. Growth requires
   raising a number in the same pull request, where a reviewer sees what
   the addition costs every project on that chain.

4. **A stale ceiling fails** — a ceiling naming a root that no longer
   resolves MUST fail, so a rename leaves a failing entry rather than a
   dead one.

5. **The cap lives in this repository, not in the templates** — a
   consuming project has no chain to measure, and answering rule growth
   with another always-loaded rule would add to the quantity it exists to
   restrain.

6. **Sizes are counted in decoded characters** — not bytes on disk, so a
   CRLF working copy and an LF one measure the same tree identically.

## Alternatives considered

- **A percentage band above the measured size** — rejected; a band is
  spent silently, and growth inside it is exactly the invisible
  accumulation the cap exists to surface.
- **A single global ceiling for all chains** — rejected; chains differ by
  a factor of nearly two, so one number is either slack for the small ones
  or an immediate failure for the large ones.
- **Failing on any drift, up or down, as the generated tables do** —
  rejected; it makes every shrinking change touch the budget file, which
  taxes the direction the project wants to encourage.
- **A rule in the templates telling consumers to budget their context** —
  rejected; it does not restrain this repository, and it grows the corpus
  to address corpus growth.
- **Reviewing tickets harder** — rejected on measurement; the tickets
  proposing core-tier rules are individually well evidenced, so the
  discipline has to act on the aggregate rather than the instance.

## Consequences

- `tests/chain-budget.txt` is added, recording 37 ceilings: 17 stacks and
  20 orthogonal roots.
- `tests/run_smoke.py` gains SYS-12, with `tests/specs/SAIT-SMK-SYS-12-001A.md`
  and a row in `tests/INDEX.md`.
- A pull request that adds a rule to a widely resolved file now carries a
  visible second change: the ceilings it raises. A 47-character addition to
  `core/quality.md` moves all 37.
- The blast radius of a core-tier addition becomes reviewable at the point
  of review rather than discoverable afterwards.
- Ceilings only ratchet down by deliberate edit; nothing lowers them
  automatically when a chain shrinks, so slack accumulates unless a
  shrinking change also lowers the number.
