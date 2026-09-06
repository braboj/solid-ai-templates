---
id: "041"
status: Accepted
date: 2026-09-06
category: tooling
supersedes: ["036"]
superseded_by: []
---

# ADR-041: Chain size is reported, not capped

## Context

Every root carried a frozen ceiling in `tests/chain-budget.txt`, and a
smoke check failed when a resolved chain exceeded it. The intent was that
a rule added to a widely resolved file could not land without a diff
stating what it costs every project on that chain.

Measured over the file's whole history at the time of this record: 32
commits touched it, moving a ceiling up 702 times and down 37. Every
raise was made in the same change as the addition that caused it, by the
author of that addition, and none was refused.

That is what a ratchet frozen at the measured size does when the measured
size is the only input. The number tells the author what they already
know — they wrote the rule and can see its length — and it tells a
reviewer a figure with nothing to compare it against, because the ceiling
was set to whatever the tree measured the last time anyone looked. A gate
whose remedy is "write the new number in this file" refuses nothing. It
records.

The cost of keeping it was not the recording. It was that the file is
generated, sorted, and touched by every branch that adds a rule, so a cut
landing several such branches conflicts on it repeatedly. Resolving those
conflicts is wrong line by line — a branch's raises were measured against
a tree that no longer exists — so the procedure was to take the upstream
file whole and re-measure, which was carried out four times in a single
release and produced no information at any of them.

Meanwhile the figure that does say something to a consumer was already
generated elsewhere. `tools/sync.py` writes chain size per stack category
into `README.md`, beside the smallest context window that still holds the
chain plus the interview, and `--check` fails when that table drifts from
the tree.

## Decision

Remove the ceiling. `tests/chain-budget.txt`, the SYS-12 check and its
specification are deleted; nothing gates chain size.

Chain size stays reported. `README.md`'s model-limits table is where a
reader meets it, `sync.py --check` keeps it honest, and the contribution
guide and playbook ask an author to read that table's diff and say in the
pull request what the addition is worth.

What that table states and a character ceiling did not is the threshold a
consumer feels: which models can still run the stack. A category crossing
from one context window to the next is a change to the stack's stated
requirements, and it is the event worth gating.

## Alternatives considered

**Keep the ceiling and raise the bar for raising it** — require a stated
justification per raise. The justification is the pull request body,
which is where it already belonged; the file adds a second place to write
it and a conflict surface to maintain it in.

**A percentage band instead of a frozen number**, so routine growth
passes and a large addition fails. Rejected when the ceiling was
introduced, for the reason that a band lets a chain grow silently until
the band is spent. That reasoning holds; it argues against the band, not
for the frozen number, and the frozen number turned out to refuse nothing
either.

**Gate the context tier instead**, failing when a root's minimum context
window changes. This is the better instrument and is filed separately. It
is not a condition of this removal: the tier is already published in
`README.md` and `sync.py --check` already fails when that table drifts,
so removing the ceiling loses no signal that the tier gate would restore.

## Consequences

- Nothing refuses chain growth. A rule added to a core-tier file lands
  when its pull request is approved, and the size it costs is visible in
  the `README.md` diff rather than in a failing check.
- Branches stop conflicting on a generated file. The re-measure procedure
  that existed only to resolve those conflicts goes with it.
- A reviewer who wants the aggregate cost reads the model-limits table,
  which states it per stack category rather than per root. That is
  coarser than 37 per-root numbers and is the granularity a consumer
  chooses at.
- The history stays legible: the deleted file's numbers remain in the
  history of every release that carried them.
