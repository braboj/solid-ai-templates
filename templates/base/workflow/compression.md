# Base — Compression Fidelity

[ID: base-compression]

## Principle

Summarising verified material is not a formatting step. It is a new
set of claims, written by whoever compressed it, and it inherits none
of the verification that backed the source.

Research gets condensed constantly: findings into a summary table,
evidence into a bullet, a paragraph into a cell, six sections into a
status report. Each pass discards the qualifiers that made the
original true. The output looks more authoritative than the input,
because short and confident reads as settled, and it is trusted more
precisely when it deserves it less.

---

## The failure mode

[ID: compression-failure]

Compression fails in three recognisable ways:

- **Over-generalisation.** Three different situations get one label
  because the label fits the majority. A comparison table summarised
  three vendors' isolation models as "shared infra"; it was accurate
  for one, wrong for the second (isolation existed but depended on a
  caller-supplied identifier) and wrong for the third (full isolation
  was available as a paid tier).
- **Qualifier loss.** "No patched version *declared in the advisory*"
  becomes "unpatched". "No *availability percentage* published"
  becomes "no SLA". The compressed form is a stronger claim than the
  evidence supports, and it is the stronger claim that gets disputed.
- **Scope drift.** A true scoped statement loses its scope and becomes
  false. "Their changelog lists no releases since October" is
  verifiable; "they have had no releases since October" is refutable
  from the package registry.

In one audit of a compressed comparison table, five of six errors came
from the compression pass. The underlying research was correct every
time.

---

## Rules

[ID: compression-rules]

- After any compression pass, you MUST re-verify the compressed
  artifact against the source, cell by cell or row by row. Verifying
  the source once does not transfer.
- A compressed claim MUST NOT be stronger than the evidence behind it.
  If the qualifier does not fit, keep the longer form.
- When a label is applied to several subjects at once, you MUST check
  it independently for each. A label that fits the majority is the
  most likely place for an error to hide.
- Where a claim is true only because of a scoping phrase, that phrase
  MUST be marked as load-bearing in the source notes, so a later edit
  does not trim it and invert the claim.
- Compression that changes a verdict, not just its wording, MUST be
  recorded with its reason, so a later pass does not silently restore
  the original.

---

## Applies to

[ID: compression-scope]

Any artifact derived from verified material rather than from the
source directly:

- comparison tables, matrices, scorecards
- summary rows in a report, executive summaries
- migration and audit checklists rolled up from per-item findings
- release notes condensed from commits
- status reports rolled up from per-task detail

---

## Rationale

[ID: compression-rationale]

The instinct is that summarising is safe because the thinking already
happened. The opposite holds: the thinking happened against the full
context, and the summary is written after that context has been
discarded.

An agent is unusually exposed here. It compresses fluently, so the
output reads well enough that neither the agent nor the reader is
prompted to check it, and the errors that survive are the confident,
tidy ones.
