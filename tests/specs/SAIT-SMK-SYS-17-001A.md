---
id: SAIT-SMK-SYS-17-001A
title: Every registered check names a spec document that exists
product: sait
type: smoke
area: SYS
priority: p2
status: ready
environment: [local, ci]
automatable: yes
created: 2026-09-07
author: Branimir Georgiev
product-version: "2.x"
tags: [tests, references, registry, index]
---

## Short description

> **Given** a check registry whose every entry names a procedure
> specification
> **When** each named specification is resolved against the documents on
> disk and against the index a reader consults
> **Then** a name matching no document fails, because the templates gate
> this class of reference for what they ship and the suite had no
> equivalent for its own

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Every registered spec names a document under `tests/specs/` and has a row in `tests/INDEX.md` |
| FAILED | A registered spec names no document on disk |
| FAILED | A registered spec has no row in `tests/INDEX.md` |
| FAILED | A registry entry carries no spec field at all |
| FAILED | The check read no registry entries or no documents |
| SKIPPED | — |
| BLOCKED | — |
| ERROR | — |

## Steps

### Prerequisites

- Repository cloned locally
- Python 3

### Setup

— (operates on the committed tree)

### Execution

1. List the `.md` documents under `tests/specs/` by stem
2. Read `tests/INDEX.md`
3. For every entry in `run_smoke.py`'s `CHECKS` registry, resolve its
   `spec` field against both
4. Report how many checks were registered and how many documents were
   read

### Assertions

1. Assert every registered spec resolves to a document on disk
2. Assert every registered spec appears in the index, so a check cannot
   be registered and stay invisible to a reader
3. Assert both counts are non-zero, per ADR-034

### Negative controls

Each control was observed failing, and each mutation was asserted to
have landed before its result was read.

1. **The defect that motivated the check.** Run against the tree as it
   stood, the check named three unresolved references — `SYS-14`,
   `E2E-01` and its own `SYS-17` — while the suite reported 31 checks
   and 0 failures. Observed 2026-09-07
2. **A renamed document.** Moving `SAIT-SMK-SYS-16-001A.md` aside MUST
   fail. Observed 2026-09-07: the on-disk count moved 58 to 57 and the
   check named `SYS-16`, so the corpus is confirmed to have changed
   rather than the message alone
3. **A document present and unindexed.** Deleting the `SYS-16` row from
   `tests/INDEX.md` MUST fail on the index half while the disk half
   passes, which is what separates the two assertions. Observed
   2026-09-07

## Related

- ADR-034 — why the counts are reported and floored
- `SAIT-SMK-SYS-01-001A` and `SAIT-INT-MNF-01-001A` — the same class of
  reference, gated for what the templates ship rather than for the suite
