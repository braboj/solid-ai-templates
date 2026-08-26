---
id: "026"
status: Accepted
date: 2026-08-26
category: process
supersedes: []
superseded_by: []
---

# ADR-026: A stale claim in a merged record is corrected by a new record

## Context

Immutability protects the decision a record makes, not its format
(#1054, #1080). A consequence surfaced as soon as that was settled: a
merged record can carry a claim that a later decision falsifies, while
every other decision in the same record remains live governance.

The folder holds one such record now. It bundles five decisions about
how decision records themselves are written and archived. Four are
current and in daily use. The fifth states that supersession metadata is
the only permitted change to a merged record and that its prose never
changes — which the later ruling makes false in both halves (#1098).

The machinery for a falsified claim is supersession, and supersession
here is whole-record. The schema check requires `status: Superseded`
exactly when the supersession link is non-empty, so a record cannot be
partly retired. A partial form was proposed and rejected (#856), on the
grounds that the invariant tying status to the link is what lets the
archived set be answered by a status filter.

That leaves three moves for a stale claim in an otherwise-live record,
and two of them are wrong:

- Editing the sentence changes what a merged record asserts, which is
  the operation immutability forbids. Performing it on the record that
  states the immutability rule compounds the problem.
- Retiring the whole record to correct one sentence bundles unrelated
  governance into its replacement and marks four working rules as
  archived.

The third is to write a new record and leave the old one alone. That
looks like doing nothing about the stale sentence, which is why it needs
stating explicitly rather than being arrived at by default.

What makes it correct is a distinction the folder has never written
down: a decision record is a dated statement of what was decided on that
date. It is not a live specification. The live specification is the
template chain, which is what a reader applies and what a generated
project inherits. A record that still says what it said in June is doing
its job; a template that says two contradictory things is a defect
(#1097).

## Decision

1. **Correct by new record** — a claim in a merged record that a later
   decision falsifies MUST be corrected by writing a new record. It MUST
   NOT be corrected by editing the record that carries it, and MUST NOT
   be corrected by appending to that record. Both change what a closed
   record asserts.

2. **Whole-record supersession means the whole record** — a record whose
   remaining decisions are current MUST NOT be marked superseded in
   order to correct one claim. Supersession is reserved for a record
   that is wholly replaced.

3. **The template chain is the authority a reader applies** — where a
   merged record and the templates disagree, the templates govern and
   the record stands as history. A correction is not complete until the
   rule is right in the template chain, and it is complete at that point
   whether or not any record was written.

4. **A correcting record MUST be complete on its own** — it MUST state
   its rule without depending on the reader having found the record it
   corrects, since prose in these records does not name other records.

## Alternatives considered

- **Edit the stale sentence in place** — rejected; changes a claim in a
  merged record, which is exactly what immutability forbids.
- **Supersede the whole record and restate its current decisions** —
  rejected; bundles unrelated governance decisions into one record
  against the one-concern rule, and archives four working rules to
  correct one sentence.
- **Append a dated addendum to the merged record** — rejected; an
  addendum adds an assertion to a closed record, and the partial-link
  machinery it would need was already considered and rejected (#856).
- **Relax the schema so a record can be partly superseded** — rejected;
  the invariant tying status to the supersession link is what makes the
  archived set answerable by a filter, and #856 settled this.
- **Do nothing, on the grounds that the template is already correct** —
  rejected; the reasoning for leaving a stale claim standing is itself a
  decision, and an undocumented one gets re-litigated by the next reader
  who finds the contradiction.

## Consequences

- `templates/base/core/docs.md` states the rule, so it reaches every
  generated project rather than only this repository.
- The decision folder may contain claims that later records correct.
  This is expected. The folder is a history; the template chain is the
  specification.
- No change to the schema check, and no change to the status invariant
  the smoke suite enforces.
- #1098 is answered without editing the record it concerns, and without
  retiring the four decisions in it that remain current.
- The open question of how to correct a stale instruction in a dated
  report (#1018) is deliberately left open. A report mixes observations
  with operative instructions, which decision records do not, so the two
  may legitimately resolve differently — but the mechanisms should be
  compared before either is settled.
