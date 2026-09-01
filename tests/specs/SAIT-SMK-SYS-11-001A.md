---
id: SAIT-SMK-SYS-11-001A
title: Prose ID references resolve in every chain carrying the file
product: sait
type: smoke
area: SYS
priority: p2
status: ready
environment: [local, ci]
automatable: yes
created: 2026-08-28
author: Branimir Georgiev
product-version: "2.x"
tags: [composition, reach, section-ids]
---

## Short description

> **Given** a template whose running prose names another file's section
> ID
> **When** every root a project can pick is resolved — each stack, and
> each orthogonal template a project opts into as its own root — and the
> chains carrying the referencing file are taken
> **Then** the file declaring that section is present in all of them —
> otherwise the reference sends a reader to a section their own context
> file does not contain

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every cross-file prose ID reference resolves in all chains carrying the referencing file |
| FAILED | A reference dangles in at least one chain, or an ID-shaped token no template declares is named |
| FAILED | The check resolved no roots, or matched no references at all |
| SKIPPED | PyYAML not installed |
| BLOCKED | — |
| ERROR | — |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3 with PyYAML

### Setup

— (operates on the committed tree)

### Execution

1. Resolve every root from the manifest: each stack, and each entry no
   stack chain reaches — the extras and platform templates a project
   opts into independently of its stack. A file reaching a consumer only
   that way sits in no stack chain, so a stack-only corpus scans it
   against zero chains and the reference passes unread
2. Map each declared section ID to the files declaring it
3. For each template, find the backticked tokens in its prose that the
   declared-ID map holds and the file does not declare itself. The set of
   IDs decides what a reference is — a pattern built from layer prefixes
   sees file-level IDs and misses the section-level ones the rule is about
4. For each such reference, compare the chains carrying the referencing
   file against those carrying the declaring file
5. Report the number of declared IDs, the number named in another file's
   prose, the references checked and the roots resolved

### Assertions

1. Assert no reference is missing from a chain that carries its
   referencing file
2. Assert the root count is non-zero — a check that resolved nothing
   reports the same empty result as one that found nothing
3. Assert the reference count is non-zero — a pattern that stopped
   matching is indistinguishable from a clean tree otherwise
4. Assert the run states how many IDs the check can see, so a pattern
   that narrows takes a visible number down with it

### Negative controls

1. Plant a reference to a section declared in a file no general chain
   carries; the check MUST fail and name the chains it is absent from
2. Alter the reference pattern so it still compiles and matches nothing;
   the check MUST fail on the reference count rather than pass. This is
   the shape a careless later edit takes, and it is the control the
   assertion in step 3 exists for
3. Narrow the pattern to a layer-prefix list; the reported reference
   count MUST drop. A widening that leaves the count unmoved changed
   nothing, whatever the pattern now reads as
4. Restrict the corpus to stack roots; the reported root count MUST drop
   and the references an orthogonal template carries MUST stop being
   checked. Three of them dangled while the check reported green

## Related

- `SAIT-SMK-TPL-04-001A` — covers EXTEND/OVERRIDE directives, which are
  structural; a prose reference is checked by neither it nor TPL-06
- `SAIT-SMK-TPL-06-001A` — the same reachability question for directives
- Measured basis, 2026-09-01: 365 declared section IDs, 29 cross-file
  prose references across 37 roots — 17 stacks and 20 orthogonal
  templates — none dangling. The prefix pattern this check used earlier
  saw 100 of those IDs and 14 of those references, and the two it missed
  in `base-typescript` dangled in three chains. The stack-only corpus
  that followed scanned `base-agents`, `base-skills` and `base-issues`
  against zero chains apiece; all three named a section their readers do
  not receive
