---
id: "021"
status: Accepted
date: 2026-08-01
category: process
supersedes: []
superseded_by: []
---

# ADR-021: Four severities, with P4 as a deferral marker

## Context

The priority scale defines five bands, `P0`–`P4`, described as
critical, high, medium, low and "Backlog — someday". Four of those are
severities; the fifth is a scheduling statement. `P4` has carried both
meanings since it was written, and the two do not compose: an issue can
be trivially small *and* urgent, or critical *and* parked.

The ambiguity stayed latent while the only implementation was GitHub
labels, which impose no structure on what a label means. It surfaced
when the scale had to map onto a tracker with a typed priority field.
Such fields offer four named severities plus an "unset" value that
means untriaged, not "lowest". Five bands cannot map onto four names
without either merging two severities or spending the untriaged slot on
a real one.

Spending the untriaged slot is the worse option in practice. In the
workspace this was measured on, 185 of 370 issues were untriaged and 22
carried `P4`; folding the latter into the former makes 22 deliberate
decisions unfindable among 185 non-decisions.

Usage across seven repositories, issues open and closed (n=482), shows
where the scale earns its keep:

| Band | Count | Share |
|------|-------|-------|
| `P0` | 10    | 2%    |
| `P1` | 47    | 10%   |
| `P2` | 124   | 26%   |
| `P3` | 279   | 58%   |
| `P4` | 22    | 5%    |

`P0` fires on 2% of issues, which is the distribution a "drop
everything" band should have — rare, not withering. `P3` and `P4`
together account for 63%, and the distinction between "low" and
"trivial" is not one the project has ever acted on.

## Decision

1. **Four severities** — the scale is `P0` critical, `P1` high, `P2`
   medium, `P3` low. `P3` MUST cover work previously described as
   trivial; "low" and "trivial" are one band.

2. **`P4` is not a severity** — it marks work deliberately deferred,
   and MUST NOT be read as a severity ranking. An issue MAY carry `P4`
   at any severity.

3. **Severity is mandatory, deferral is not** — every issue MUST carry
   exactly one of `P0`–`P3`. `P4` is optional and additional.

4. **On a tracker with a typed priority field**, `P0`–`P3` MUST map
   onto the four named values in order, and the unset value MUST mean
   untriaged. `P4` MUST NOT consume the unset value; it is carried as a
   label, a milestone, or the tracker's own deferral mechanism.

## Alternatives considered

- **Collapse `P0` into `P1`** — rejected; it merges "stop other work"
  with "take next" to solve a problem at the opposite end of the scale,
  and discards the one band whose rarity is evidence it is working.
- **Keep five severities, map `P4` to the unset value** — rejected;
  deliberate deferrals become indistinguishable from untriaged issues,
  which outnumber them roughly eight to one.
- **Keep five severities and let platforms diverge** — rejected; the
  point of defining the scale centrally is that a band means the same
  thing wherever it is read.
- **Drop `P4` entirely** — rejected; deferral is real and needs a
  marker. Removing it pushes the information into prose, where it stops
  being filterable.

## Consequences

- `base/workflow/issues.md` restates the priority table with four
  severities and `P4` as a deferral marker.
- `platform/github.md` and `platform/linear.md` restate their priority
  sections; the Linear mapping table drops its `P4` row from the native
  field.
- `CLAUDE.md` §2.2 restates the priority label meanings.
- Existing `P4` issues keep their label and gain a severity. Projects
  MUST assign one rather than inferring it, since `P4` never encoded a
  severity in the first place.
- Tooling that treats `P0`–`P4` as a single ordered enum needs to treat
  `P4` as orthogonal instead.
