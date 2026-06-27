---
id: "019"
status: Accepted
date: 2026-06-27
category: tooling
supersedes: []
superseded_by: []
---

# ADR-019: Redundancy detection as an exact, override-aware CI gate

## Context

Templates compose into resolved chains. A rule stated in two active
sections of the same chain dilutes the agent's attention — the project's
primary, and largely only, controllable quality lever. Smoke validated
structure (references, IDs, manifest parity) but never content overlap,
so duplication accumulated silently: two core-tier files restated each
other's testing rules, and three Python framework stacks restated a
migration rule already provided by their parent.

The composition model complicates detection. A section tagged
`[OVERRIDE: id]` legitimately repeats the section it replaces, so a naive
scan of raw template files reports those repeats as duplicates — a
throwaway probe did exactly this, flagging the Go Stack sections that the
override model produces by design.

## Decision

1. **Detect on the resolved chain** — fingerprint rule bullets per
   section across each stack's resolved chain; a duplicate is a
   normalized rule appearing in two active sections of one chain.
2. **Exclude override-superseded pairs** — a duplicate where one section
   `[OVERRIDE]`s the other's ID, directly or transitively, is the
   composition model working as designed and MUST NOT be reported.
   Sibling-`[EXTEND]` and unrelated duplicates ARE reported.
3. **Gate exact duplicates only** — `--check` MUST fail CI on
   exact-normalized duplicates. Near / paraphrase duplicates (`--near`)
   are an audit aid, not a gate.
4. **Ratchet from a baseline** — `--check` MUST fail only on duplicates
   not in a `BASELINE` allowlist, each entry keyed to its owning issue,
   and SHOULD report any baseline entry that no longer applies. The
   baseline shrinks toward zero as issues clear.

## Alternatives considered

- **Fuzzy / near-duplicate CI gate** — rejected; paraphrase thresholds
  are subjective and produce false positives; kept as a manual audit.
- **Raw-file duplicate scan** — rejected; over-reports `[OVERRIDE]`
  sections; the override graph is required to be trustworthy.
- **Zero-gate from day one** — rejected; the library carried known
  duplicates owned by other issues; a baseline ratchet ships protection
  immediately without forcing premature changes.
- **A smoke check in `run_smoke.py`** — rejected as the home; the audit
  needs chain resolution and an optionally slow near pass, so it lives
  in its own tool wired into CI alongside smoke.

## Consequences

- New tool `tools/audit_redundancy.py`; new CI step in
  `.github/workflows/smoke.yml` runs `--check`.
- A new in-chain exact duplicate fails CI; a contributor MUST fix it or
  add it to `BASELINE` with its owning issue.
- Resolving a baselined duplicate requires removing its `BASELINE`
  entry; `--check` reports a stale entry to prompt this.
- Documented in the PLAYBOOK "Audit redundancy" procedure and the
  CLAUDE.md command catalogue.
- `BASELINE` is currently empty — the gate enforces a true zero.
- Near-duplicate detection remains advisory, not gated.

## Related

- `docs/meta/template-content-quality.md` — the attention-dilution
  rationale this gate operationalizes.
