# Base — Documentation

[ID: base-docs]

## Rule language

All rules use the key words defined in **RFC 2119** to indicate requirement
levels. Every rule MUST use one of these words:

| Word       | Meaning                                                         |
| ---------- | --------------------------------------------------------------- |
| MUST       | Absolute requirement — no exceptions without explicit rationale |
| MUST NOT   | Absolute prohibition                                            |
| SHOULD     | Recommended — deviations require justification                  |
| SHOULD NOT | Not recommended — may be ignored with justification             |
| MAY        | Optional — developer decides without further discussion         |

## Single source of truth

- `README.md` is the single source of truth for project structure
- Do not duplicate structure in other documents — reference `README.md` instead
- Agent context files (`CLAUDE.md` / `AGENTS.md`) keep their Project
  structure section as a pointer to the README section plus
  agent-specific placement rules — never a second directory tree
- No references to non-existent files, components, or services

## Standard documents

| File                  | Purpose                                                                |
| --------------------- | ---------------------------------------------------------------------- |
| `README.md`           | Project overview, structure, setup, commands                           |
| `CLAUDE.md`           | AI agent context and project rules                                     |
| `docs/ONBOARDING.md`  | Onboarding guide for new contributors                                  |
| `docs/PLAYBOOK.md`    | Operational reference for common tasks                                 |
| `docs/dev-journal.md` | Development history and session log (MUST for agent-assisted projects) |
| `docs/SPEC.md`        | System design, architecture rules, composition model (SHOULD for complex projects) |
| `CHANGELOG.md`        | Released versions and what changed in each (MUST for a project that publishes versions) |

Guide-doc filenames follow a deliberate casing split: single-word guide
docs use SHOUT-case (`README.md`, `CLAUDE.md`, `ONBOARDING.md`,
`PLAYBOOK.md`, `SPEC.md`); multi-word descriptive docs use lower
kebab-case (`dev-journal.md`). This is intentional, not drift.

### Community health files

- A public repository MUST carry `SECURITY.md`. Public code attracts
  vulnerability reports whether or not the project invites them, and with
  no stated route a finder either discloses publicly or stays silent
- A repository that accepts outside contributions MUST carry
  `CONTRIBUTING.md`. What makes it required is the issue tracker or pull
  requests being open to people without commit rights, not the repository
  being public
- `CODE_OF_CONDUCT.md` MAY accompany a public interaction surface —
  issues, discussions. It is a governance choice rather than a safety
  one, and a project without it still has a disclosure route and a
  contribution path, which is not true of the two above it. Declining
  it owes no recorded justification. A project adopting it names who
  enforces it, since a code of conduct nobody enforces is a commitment
  the project has not met
- A private repository with no outside contributors needs none of the
  three
- `SECURITY.md` names a private disclosure route and the versions that
  receive fixes. A public issue tracker is not a disclosure route, since
  filing there IS the disclosure

#### SECURITY.md structure

`base-readme` gives the other front-door document nine required sections
in a stated order. Both files are read by a stranger arriving at the
repository, and a required document with no stated structure is one whose
quality varies by author. These are the sections, in order:

1. **Disclosure route** — MUST. Where to send a report privately, and
   explicitly that the tracker is not it
2. **Supported versions** — MUST. Which versions receive fixes, as a
   rule a reader can apply to their own version rather than a list that
   goes stale
3. **Scope** — MUST for a project with any deliberate unsafe surface,
   SHOULD otherwise. Absent a scope section every report is in scope,
   including reports about behaviour the project offers on purpose. A
   library exposing weak settings as explicit test arguments will be told
   they exist, and has nothing to point at when declining
4. **Acknowledgement expectation** — MUST, stated as a duration the
   project chooses rather than a number inherited from here. A finder who
   has heard nothing for a week cannot tell a slow maintainer from a dead
   channel, and public disclosure is the documented next step in most
   disclosure norms
5. **What a report should contain** — SHOULD. Version or commit,
   reproduction, impact. Cheap to state, and the difference between a
   report that can be triaged and one that needs three round trips

A private repository, or one with no external attack surface, is held to
the first two only — the rest describe a relationship with outside
finders that such a project does not have.

The placement check above stays a placement check. It verifies each file
resolves to exactly one recognised location and deliberately does not
read inside them: section presence is a different question, and folding
it in would make a passing placement check mean something it was not
written to mean.
- Code hosts recognise three locations, in this precedence: `.github/`,
  then the repository root, then `docs/`. Put the files at the root by
  default — a first-contact document belongs where a visitor lands
- Each file lives in exactly one recognised location. A copy in two of
  them means the host serves the first and the other rots unread, with
  nothing in either file saying which one is live
- Check — every required file resolves to exactly one recognised
  location. Scope: a public repository that accepts outside
  contributions; a private repository with no outside contributors is
  outside what this checks. Pass condition: the command reports how many
  names it checked and prints nothing after that:

  ```bash
  py - <<'EOF'
import pathlib
DIRS = (".github", ".", "docs")
REQUIRED = ("SECURITY.md", "CONTRIBUTING.md")
NAMES = REQUIRED + ("CODE_OF_CONDUCT.md",)
print("community health files checked: %d" % len(NAMES))
for name in NAMES:
    homes = [d for d in DIRS if pathlib.Path(d, name).is_file()]
    if len(homes) > 1:
        print("%s: in %s - the host serves %s and the rest rot"
              % (name, ", ".join(homes), homes[0]))
    elif not homes and name in REQUIRED:
        print("%s: absent from .github/, the root and docs/" % name)
  EOF
  ```

## Numbering

- Use numbered headings (1, 1.1, 1.2, 2, 2.1, etc.) in PLAYBOOK and
  ONBOARDING — this enables cross-referencing between documents
  (e.g. "see PLAYBOOK 2.4")

## ONBOARDING structure

`docs/ONBOARDING.md` MUST contain the following sections in order:

1. **Prerequisites** — required tools and versions (Node, Python, Docker, etc.)
2. **First-time setup** — clone, install, configure (copy-pasteable commands)
3. **Verify the setup** — how to confirm everything works (run dev server,
   run tests, expected output). Verify step descriptions SHOULD be
   re-checked when the default route (`/`) or landing page changes —
   a content change can invalidate the expected output without triggering
   a "setup changed" check. Structure audits MUST verify that verify
   steps produce the described output.
4. **Key files** — table of files a new contributor should read first
5. **Project context** — brief domain overview and links to architecture docs
6. **Daily workflow** — cross-reference PLAYBOOK sections, do not duplicate

## PLAYBOOK structure

`docs/PLAYBOOK.md` MUST contain the following sections in order:

1. **Git workflow** — branch, commit, PR, merge, issues
2. **Domain operations** — how to add/modify the project's core data or
   entities (project-specific — e.g. "add a catalog entry", "add a migration")
3. **Quality** — testing, CI checks, linting, link checking, secret
   scanning, and other quality verification workflows; manual verification
   tools (analytics, search indexing, SEO crawls, performance field data)
   belong here alongside automated checks — list automated first, manual
   last
4. **Maintenance** — update dependencies, quality conventions, ADRs
5. **Release and deploy** — release process, tagging, deployment

Projects MAY add sections beyond these five (e.g. "Observability",
"Infrastructure") — append them before Release and deploy, which MUST
remain the last section.

Subsection headings SHOULD follow the pattern **"what it checks (tool
name)"** — e.g. "Secret scanning (gitleaks)", "Type checking (astro
check)". Description-first naming keeps the section scannable regardless
of tool changes.

## Documentation rule

Before every commit, update all relevant documentation:

- **`CLAUDE.md`** — update if architecture, stack, design rules, or conventions
  change
- **`README.md`** — update if project structure, stack, or setup steps change
- **`docs/PLAYBOOK.md`** — update if commands, workflow, or release process
  change
- **`docs/ONBOARDING.md`** — update if the contributor workflow changes

### When a document disagrees with the system

A project document that contradicts the live state of the system it
describes is not automatically the authority. Establish which one is
wrong before changing either.

- MUST check whether the rule is inherited. A document generated from a
  template can drift from the template while the system still matches
  it — in which case the document is stale and the system is correct
- MUST NOT act on the document's reading alone when the observed state
  is defensible. Acting first destroys a correct configuration to
  satisfy a sentence that was already out of date
- The order is: read the document, observe the system, then find the
  rule that governs both. Reconcile to whichever the governing rule
  supports, and fix the other

## Decision logs

- Significant architectural decisions MUST be recorded as Architecture Decision
  Records (ADR) in `docs/decisions/`
- Each ADR documents: context, decision, alternatives considered, consequences
- Each ADR MUST address exactly one concern — a separate concern gets its
  own ADR. One concern is not one rule: a single ADR MAY number multiple
  related decisions (1., 2., …) within its one concern
- Render "Alternatives considered" and "Consequences" as tables where the
  content fits — they scan faster than prose lists
- ADRs are immutable once merged — create a new ADR to supersede an
  old one. Two changes are exempt: the supersession metadata
  (`status`, `date`, `superseded_by`), because a supersession has to
  be recorded on both sides; and format-only edits to the body, which
  move no claim
- What is immutable is the decision, not the format. The decision is
  the set of claims the record makes in Context, Decision,
  Alternatives considered and Consequences. Adding a claim, removing
  one, or changing what one asserts requires a new ADR, however
  small the edit looks
- Reformatting a merged ADR therefore needs no superseding ADR. The
  test is whether any claim moved, not whether the edit appears on a
  list of permitted operations: rewrapping to the project width,
  normalizing headings, titles, filenames and cross-links, splitting
  a sentence no reader can parse, and rendering a buried enumeration
  as a list all qualify. State "format-only, no decision change" in
  the commit, and show it with `git diff --word-diff` — only
  whitespace, connectives, capitalisation and list rendering may
  move. An enumeration of allowed operations would be
  under-inclusive by construction, and it would leave an unreadable
  record unreadable in the name of protecting it
- A claim in a merged ADR that a later decision falsifies is corrected
  by writing a new ADR, never by editing the ADR that carries it and
  never by appending to it — both change what a closed record asserts.
  An ADR whose remaining decisions are current MUST NOT be marked
  `Superseded` to correct one claim; supersession is for a record that
  is wholly replaced
- Precedence between a project's own decision records and the rules it
  inherits is that project's decision, and MUST be declared in its
  context file. A record documenting a deliberate divergence from an
  inherited rule is such a decision: it carries the reasoning the
  divergence rests on, so a later version of that rule does not retire
  it. The inverse holds only in a repository that owns the rules it
  applies, where a record describes a rule rather than departing from
  one — that ordering belongs in its own context file, not here
- When an ADR's premise is refuted shortly after it merges (typically by
  data that should have informed it), prefer a same-day or same-week
  supersession ADR documenting the post-mortem over silently closing the
  follow-up issues — an `Accepted` ADR describing code that does not exist
  is documentation-vs-code drift. The supersession ADR records the refuting
  evidence and a post-mortem (Symptom / Root cause / Why missed / Fix /
  Prevention) if the original shipped any change; the superseded ADR's
  status flips to `Superseded` and gains the new id in
  `superseded_by`, in the same PR
- When a rule the project deliberately does NOT follow moves in its own
  source — an upstream chain, a vendored rule set, a submodule pointer
  bump — re-read the divergence record before deciding what the change
  means. The reconciliation is done by reading a diff, and the diff does
  not know the divergence exists, so the change reads as a gap to close
  rather than a decision already reasoned about
- A reconciliation that touches a recorded divergence MUST state whether
  the divergence still holds, and MUST separate what the range refuted
  from what it merely moved nearby. A decision can survive intact while
  a neighbouring rule it named — a fallback, an alternative mechanism,
  an exemption it relied on — is deleted; that is a repair to the
  record, not grounds to reverse it. Recency is no protection, since
  the source can move within hours of the record merging
- File naming: `NNN-slug.md` — zero-padded sequence number + kebab-case slug
  (e.g. `001-data-storage.md`, `002-hosting.md`)
- ADR file format — YAML frontmatter carrying the machine-readable
  metadata, then the prose body:

```markdown
---
id: "NNN"                 # zero-padded sequence, quoted to stay a string
status: Proposed          # Proposed | Accepted | Superseded
date: YYYY-MM-DD          # date the status was last changed
category: process         # one value from the project's closed set
supersedes: []            # ids this ADR supersedes
superseded_by: []         # ids that supersede this ADR
---

# ADR-NNN: Title in sentence case

## Context

[Why this decision was needed]

## Decision

[What was decided]

## Alternatives considered

[What was rejected and why]

## Consequences

[What follows from this decision]
```

- The frontmatter is the source of truth for status, date and
  supersession links. Do NOT also carry a prose `## Status` section or
  `**Status:**` / `**Date:**` lines — a second copy drifts from the
  first and nothing says which one won
- `id` MUST match the filename's leading digits, and MUST be quoted so
  a leading zero survives as a string rather than parsing as a number
- `status` MUST be one of `Proposed`, `Accepted`, `Superseded`, and
  MUST read `Superseded` if and only if `superseded_by` is non-empty
- `date` MUST be present and MUST be updated whenever `status` changes
- `category` MUST come from a closed set the project defines and
  records. A new category needs its own ADR, which keeps the set a
  scope-of-impact decision instead of a free-text field
- `supersedes` and `superseded_by` MUST both be present even when
  empty, so a reader never has to tell absent from empty
- Check — every ADR parses and satisfies the schema. Pass condition:
  the command reports how many records it inspected and prints nothing
  after that. A count of zero is a failure, not a clean folder: the glob
  selects on a numeric prefix, so moving the directory or changing the
  numbering convention reduces it to no matches while it keeps reporting
  success. Run it after adding or superseding an ADR, and wire it into
  CI beside the other document gates:

  ```bash
  py - <<'EOF'
import pathlib
KEYS = ("id", "status", "date", "category", "supersedes", "superseded_by")
STATUS = ("Proposed", "Accepted", "Superseded")
records = sorted(pathlib.Path("docs/decisions").glob("[0-9][0-9][0-9]-*.md"))
print("decision records inspected: %d" % len(records))
if not records:
    print("no decision records found; the naming convention drifted")
for f in records:
    lines = f.read_text(encoding="utf-8").splitlines()
    fm = {}
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            key, sep, val = line.partition(":")
            if sep:
                fm[key.strip()] = val.strip()
    date = fm.get("date", "")
    linked = fm.get("superseded_by", "[]") not in ("[]", "")
    if not (all(k in fm for k in KEYS)
            and fm.get("status") in STATUS
            and len(date) == 10 and date.replace("-", "").isdigit()
            and (fm.get("status") == "Superseded") == linked):
        print(f)
  EOF
  ```

- Do NOT maintain a monolithic architecture document that mixes decisions,
  data model specs, and migration tracking — decisions go in ADRs, data
  model is the code (`src/types/`), migration tracking belongs in the
  dev journal or issue tracker
- ADRs MUST NOT cite other ADRs in their prose body — the only
  ADR-to-ADR links are the frontmatter `supersedes` and
  `superseded_by` fields, which are the only ones a check can
  validate. Prose references rot silently, and a forward reference
  to an ADR that does not exist yet cannot be written at all. The
  prohibition binds records authored after the project adopts it —
  records merged beforehand keep their prose citations, per Amending
  a record below
- A `## Related` section MAY close an ADR with context-only
  pointers. It MUST NOT carry decision-bearing text: moving or
  superseding anything it names MUST NOT change what the Decision
  section means
- Implementation details (phrase tables, templates, worked examples) belong
  in the ADR itself, not in separate spec files — external specs create
  maintenance burden and go stale
- Non-trivial ADRs SHOULD include at least one inline ASCII diagram or
  mockup in the Decision section — a pipeline flow, layout sketch,
  state transition, or similar — so the concept is scannable without
  parsing dense prose. A diagram MUST stay legible in a monospace
  font and MUST NOT rely on colour or proportional spacing. Plain
  ASCII (`+`, `-`, `|`) and Unicode box-drawing both satisfy that,
  so use whichever reads better. Example:

  ```
  +---------------------+---------------------+
  |   original input    |    rendered output  |
  +---------------------+---------------------+
  |        overlay: rendered on original      |
  +-------------------------------------------+
  ```

  Use the project's preferred rendered-diagram format (Mermaid,
  Draw.io) for diagrams that need to be standalone artifacts; inline
  ASCII is for the quick concept aid that lives inside the ADR
- Creating a new directory or moving content between documents is an
  architectural decision — write the ADR **at the moment of the decision**,
  before creating the files

### Findings docs

When a threshold, parameter, or constant is picked from data rather
than from first principles, document the run that produced the
number in a **findings doc** co-located with the data it describes.

Findings docs are not ADRs. ADRs record *decisions*; findings docs
record the *observations* that load-bearing constants depend on.
Findings docs are not dev journal entries either — the dev journal
captures session history, while a findings doc is an accumulating
reference for a specific subsystem's empirical numbers.

- A findings doc lives next to the data/source it describes — e.g.
  `metrics/latency.md` alongside `metrics/latency.py`, not
  in a project-level `docs/` directory
- Format: a short header, a "How to reproduce" section naming the
  command that produced the numbers, then one section per dated
  run — each with raw output (or a verbatim summary) and numbered
  findings interpreting it
- Every PR that materially changes the numbers MUST update the
  findings doc in the same PR — the threshold in code and the
  observation backing it land together
- Reference the findings doc from the source where the constant is
  defined (a one-line comment naming the file is enough) so a
  future reader can trace why the constant has the value it does
- Backfilling a provenance or justification doc — one whose job is to
  justify a stored value against a cited source (a scoring-log, a
  data-provenance table) — is a data audit, not transcription: writing
  "field = X because source says Y" is the moment to cross-check X
  against Y. Surface a discovered gap or inconsistency (fix it or file
  it), never encode it as a false "not tested" marker. Distinguish
  "source silent on the field" (legitimately undefined) from "source has
  data, record unpopulated" (a data gap, not an untested field)

Example skeleton:

```markdown
# Cache TTL — findings

## How to reproduce
`py -m mymodule.cache --measure-staleness`

## 2026-05-12 — initial pass (1,200 keys)
<raw output snippet>

1. 99% of keys are unchanged past 300s; staleness cost climbs sharply
   after 600s — keep CACHE_TTL_SECONDS at 300
2. ...
```

## Amending a record

[ID: docs-record-amendment]

A record whose job is to say what happened — a decision record, a dated
report, a journal entry — is fixed in what it claims, not in its bytes. The
test for any edit is whether it changes what the record claims happened. If
it does, it is an amendment and MUST go in a new record; if it does not, it
is a correction and is made in place with no marker.

### Scope of a form rule over an immutable corpus

- A rule constraining the FORM of a document class whose members are
  immutable once merged — a citation ban, a heading convention, a required
  section, a naming scheme — MUST state whether it binds forward or
  retroactively. The two readings differ by an unbounded amount of work and
  by whether the existing corpus is compliant or in violation
- Absent a statement the rule binds forward: records merged before the
  project adopted it keep their form, because immutability outranks a form
  rule that arrived later
- Record the boundary the rule starts at — a date, or the first record id it
  binds — and gate from there, so the untouched history is visibly in scope
  of nothing rather than reading as standing debt the next reader files
- Do NOT migrate the corpus to satisfy such a rule. What the rule targets is
  frequently load-bearing inside a Decision section, so the rewrite moves a
  claim and the format-only exemption does not cover it. Superseding each
  affected record is worse — it produces a supersession that changes no
  decision

### Dated reports

- A dated report — an audit, an incident write-up, a review — mixes two kinds
  of content with opposite lifespans. Observations are what was measured on
  the date and are immutable in the sense an ADR is. Operative instructions —
  a condition for lifting a redaction, a re-review trigger, a "revisit when X
  ships" — govern future behaviour, and can become unfulfillable when the
  world moves
- Correct a stale instruction with a dated addendum stating what changed,
  which instruction it supersedes, and that the observations are deliberately
  left as written. Rewriting the sentence silently changes a dated
  observation to match a later decision; leaving it makes the report issue an
  instruction nobody can discharge, which every later reader re-derives as
  stuck
- A grade, score or severity in a dated report is an observation, not an
  instruction. It is NOT re-derived when the underlying facts change — the
  closed report keeps its number and a later report derives its own
- The addendum is available because a report has no supersession chain. It
  MUST NOT be used on an ADR: appending to a merged decision record changes
  what a closed record asserts, and the Decision logs section above already
  routes that correction through a new record instead
- An observation MAY be stated as a command and its output, and that is
  the strongest form one takes — a claim a later reader can falsify in a
  single command. It is also the only form that the act of recording it
  can refute. Where the command ranges over a moving reference, its
  answer changes the moment the commit carrying the report lands, so the
  record and the commit falsifying it are the same commit. `HEAD` and
  the working tree are the two common ones; "the latest tag" and "the
  current branch" are the same defect wearing a different name
- Such a command MUST be scoped so that committing the record cannot
  change its answer: name the commit or tag the claim is about, never a
  reference that moves with the record. Where the claim is genuinely
  about the state before the record landed, it says so and names that
  commit
- No addendum is owed for one of these. The addendum above repairs an
  instruction the world made unfulfillable, and nothing about the world
  moved here — the claim was wrong when written. The remedy is the
  scope, and a note explaining a wrong scope leaves the wrong scope in
  place
- This governs what a document asserts, not when a check runs. Whether a
  check is executed before or after the change it gates — and whether it
  reads committed or staged work — is a property of the run, decided
  once and observed immediately. A claim written into a report is
  durable, is read by people who were not there, and is the thing this
  rule protects
- Which documents are dated reports is a judgement, so this constraint
  stays declarative. A locator for commands naming a moving reference
  would report every procedure and runbook that correctly tells a reader
  to run one against their own tree, and a finding a reader has to
  dismiss on every run is the failure the reporting rules exist to
  prevent

### Retiring a document

- Retiring a document does not retire what it says. Scope the removal by
  searching the tree for the CONTENT — the incident, the identifier, the
  material — never by deleting the file named for it
- The journal is the surface most likely to be missed: it is append-only,
  organised by date rather than by topic, and its post-mortems routinely
  restate an incident in more detail than the report that triggered it
- Where a surviving copy is sensitive, state the finding to whoever owns the
  repository rather than widening the deletion unasked. What a repository
  publishes is that owner's decision
- The concept-retirement sweep in `templates/base/core/quality.md` does not
  cover this. That rule chases surviving instructions to APPLY a retired
  concept and explicitly settles for historical records; a record is exactly
  what carries the content here

## Release changelog

A project that publishes versions MUST carry `CHANGELOG.md`. Follow Keep a
Changelog over semver headings: one section per released version, newest
first, each with a version and a date, grouped under Added, Changed,
Deprecated, Removed, Fixed and Security. An `Unreleased` section at the top
collects work since the last release.

A per-version record published by the code host does NOT discharge this.
Generated release notes are derived from merged pull request titles, so
their entry form is whatever those titles were: no grouping, no bound, and
no statement of what a reader must do. A pull request title is written for
a reviewer who has the diff; a changelog entry is written for someone
outside the project deciding whether to upgrade. They are different
audiences, which is the same distinction this section draws between the
changelog and the journal — so the requirement is a committed file, and a
release page is where it may additionally be published, never where it may
instead live.

The committed file also outlives the host. It is present in a clone, a
mirror, a vendored copy and an offline archive, and it is versioned
alongside the code it describes; a release page is none of those things.

- An entry states **what changed and what a reader must do about it**, and
  nothing else. It is the one document in the set whose reader is outside
  the project and is deciding whether to upgrade
- Reasoning belongs in a decision record, the session belongs in the
  development journal, and the review belongs in the pull request. An entry
  MAY point at any of them; it MUST NOT reproduce them
- A breaking change MUST say what breaks and name the migration, not only
  that the interface moved
- An entry MUST NOT exceed 40 words. That is a bound on the form, not a
  style preference: past roughly that length an entry has started
  explaining rather than stating, and the reader deciding whether to
  upgrade has to finish a paragraph to find out
- The `Unreleased` section is maintained by the change that causes it. A
  change that a reader outside the project would want to know about adds
  its entry in the same pull request that makes it, and a change that
  needs no entry says so in the pull request rather than staying silent —
  silence and "not notable" look identical at release time, and only one
  of them is true
- A project adopting the changelog after it has already published versions
  starts its first section at the version being released next, and records
  the earlier ones by naming where they are published. It MUST NOT
  reconstruct them from pull request titles: that is the reviewer-facing
  form this section rejects, and a file of it would satisfy the check while
  failing the rule's premise. Every version released after adoption gets
  its own section, so the reference covers a closed set that never grows

This is the one document class where an unspecified rule does not stay
unspecified. Where a document class carries no rules and a neighbouring
class is specified in detail, the unspecified one inherits the neighbour's
voice, because the neighbour is the only model available to whoever writes
the first entry. The development journal below is specified in detail and
sits one section away. A changelog drifting toward journal prose is the
predictable outcome, and it was the observed one: across 37 entries in a
downstream project, 16 ran over 40 words and the longest two were 108 and
142 words — paragraphs of reasoning about why a change was made, in a
document whose reader wanted to know whether to upgrade.

The two are not the same document. The journal records a session and is
fixed once written; the changelog records a release and is read by someone
outside the project. Neither may be generated from the other.

A rule bounding a form needs a check, or the bound decays to advice:

```bash
py - <<'EOF'
import pathlib, subprocess

LIMIT = 40
path = pathlib.Path("CHANGELOG.md")

# A missing file means two different things. Ask the repository which,
# rather than skipping both alike.
tags = subprocess.run(["git", "tag"], capture_output=True,
                      text=True).stdout.split()
print("release tags found: %d" % len(tags))

if not path.is_file():
    if tags:
        raise SystemExit("%d versions published and no CHANGELOG.md"
                         % len(tags))
    print("no versions published and no CHANGELOG.md - nothing to check")
    raise SystemExit(0)

# An entry is a bullet plus the lines it wraps onto. Measuring physical
# lines instead reads only the first line of a wrapped entry, and a file
# wrapped to any column then reports every entry as under any limit.
entries, current = [], None
for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1):
    if line.startswith("- "):
        if current:
            entries.append(current)
        current = [number, line[2:].strip()]
    elif current and line.strip() and not line.startswith(("#", "-")):
        current[1] += " " + line.strip()
    elif not line.strip():
        if current:
            entries.append(current)
        current = None
if current:
    entries.append(current)

print("changelog entries measured: %d" % len(entries))
print("word limit: %d" % LIMIT)
over = [(n, len(t.split()), t) for n, t in entries if len(t.split()) > LIMIT]
print("entries over the limit: %d" % len(over))
for number, count, text in over:
    print("  line %d: %d words - %s..." % (number, count, text[:60]))
EOF
```

Pass condition: the check prints the tag count, how many entries it
measured and the limit it applied, then `entries over the limit: 0`. A
measured count of zero is a failure rather than a clean file — it means the
entry marker did not match the file's bullet style, and every entry went
unread.

The tag count is what separates the two absences. A project that has
published nothing legitimately has no changelog; one that has published
versions and has no changelog is in breach, and before this line both
printed the same skip and exited clean. An absent file is the one state a
check is most likely to wave through, because there is nothing in it to
find fault with.

The unit is the entry, not the line. A word bound measured against
physical lines is defeated by wrapping: in a file wrapped to any column
the first line of every entry falls under any limit, and the check reports
a clean file while reading a fraction of each entry it counted. The first
changelog written against this rule had three entries of 45, 41 and 42
words and the line-based measurement reported none of them. A check whose
unit is finer than the rule's unit does not under-report by a little — it
reports the wrong thing entirely, at full confidence.

## Development journal

- Projects using agent-assisted development MUST maintain a
  `docs/dev-journal.md`
- Agents have no persistent memory across sessions — the journal provides
  continuity by recording what was done, what changed, and why
- Structure: architecture overview at the top, then session entries in
  chronological order (oldest first, newest at the bottom)
- Session entry heading format: `## YYYY-MM-DD — Short theme` (3-6 word
  theme; a parenthetical qualifier such as `(evening)` is allowed when a
  single day has multiple sessions)
- Each session entry MUST record, as bold-labelled fields: **Tool** used,
  **Key changes**, **PRs merged**, **Issues closed/created**, and
  **Lesson** or decisions made (linking ADRs for any decision); the date
  lives in the heading. Add a **post-mortem** when the session shipped a
  P0/P1 fix or handled an incident (see below)
- When milestones or phases are renamed or renumbered in the issue tracker,
  the dev journal architecture overview MUST be updated in the same PR
- Do not duplicate content that belongs elsewhere — link to ADRs for
  decisions, link to issues for task tracking, do not repeat data model
  specs that live in code
- A journal entry's ACCOUNT is fixed: what a session changed, why a
  decision went the way it did, what it got wrong, and what it left
  undone. A later entry corrects an earlier one; the earlier one is not
  rewritten
- A cross-reference is not part of that account. It says where something
  is now, makes no claim about the session, and is corrected in place
  with no amendment marker. Continuity for an agent with no memory is
  the job this document is given above, so a stale pointer defeats its
  stated purpose — and under a blanket immutability reading the breakage
  accumulates, since every later move of a cited target adds another
  dead reference permanently
- The "not done" or follow-ups list is account, not pointer. A carried
  item is closed by the next entry saying so, never by editing the entry
  that raised it — tidying the old list is the tempting move and the
  wrong one
- When writing a new entry, follow the document-convention-matching
  rule in `templates/base/workflow/ai-workflow.md` (Match document
  convention section) — read prior entries and copy their skeleton
  exactly; the prior entry is the authoritative structural template
- That rule governs an entry's SHAPE, never the file's ordering.
  Ordering comes from the rule above and nowhere else. Copying it
  from the file makes a violation permanent: a journal that starts
  newest-first stays newest-first, and every compliant session adds
  another entry in the wrong place. The ordering of a long file is
  also invisible in a diff that appends one entry, so review does
  not catch it either — which is why it is checked:

  ```bash
  py - <<'EOF'
import pathlib, re

# Session headings only, and only outside fenced blocks so a quoted
# example is not mistaken for an entry.
HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2})\b")
path = pathlib.Path("docs/dev-journal.md")
entries, fenced = [], False
for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
    if line.lstrip().startswith("```"):
        fenced = not fenced
        continue
    if fenced:
        continue
    found = HEADING.match(line)
    if found:
        entries.append((number, found.group(1)))
print("session entries inspected: %d" % len(entries))
if not entries:
    print("%s: no session entries found; check the heading format" % path)
for (before_n, before_d), (after_n, after_d) in zip(entries, entries[1:]):
    if after_d < before_d:
        print("%s:%d %s follows %s at line %d; entries run oldest first"
              % (path, after_n, after_d, before_d, before_n))
  EOF
  ```

  Pass condition: the command reports how many entries it inspected and
  prints nothing after that. It reports an empty result as a failure
  too, since no entries found means the heading format drifted rather
  than the file being in order

### Post-mortems

P0/P1 bugs and all incidents MUST include a post-mortem in the dev
journal session entry. The trigger is the item's severity, not its
outcome — a P0/P1 closed as NOT PLANNED carries one too. Format:

- **Symptom:** what the user saw
- **Root cause:** what was actually wrong
- **Why missed:** what review or test gap allowed it
- **Fix:** what was done and what was deliberately not done, with a PR
  reference wherever one shipped
- **Prevention:** what was changed to catch it next time

Not needed for minor fixes or cosmetic bugs. The purpose is to produce
actionable prevention steps — a post-mortem without a prevention action
is incomplete.

An accepted risk needs the entry more than a fix does. The code shows
nothing, the diff shows nothing, and the tracker shows a closed issue
with a terse reason, so the reasoning for accepting is the only thing a
future reader has. Two fields carry it:

- **Fix** records the split. Partial remediation is the common case —
  rotate the credential, decline to purge the history — and which half
  went which way is the substance
- **Prevention** records the compensating control that makes the
  acceptance safe, and NAMES the premise it rests on ("nothing trusts
  this", "no consumer reads that path"). When the premise stops holding
  the acceptance stops holding, and nothing else in the repository
  records that dependency

## Writing style

- Markdown wraps at the width the project declares in configuration,
  never at a width written into a rule. A document is not code and
  does not inherit the source line limit; it gets its own, and the
  project chooses the number
- Declare the width ONCE — in the Markdown linter's configuration or
  in `.editorconfig` under the Markdown section, not both. A second
  copy drifts from the first and nothing says which one won
- The exemptions travel with the declaration. Which of fenced blocks,
  table rows and headings are excused is part of the configured rule,
  not a convention each author infers
- Two exemptions are structural rather than configured, because the
  line cannot be wrapped at all and no configuration expresses that.
  The first is a bracketed single-line directive a parser reads whole,
  such as a template's dependency header. Wrapping it changes what it
  means, so the check skips it wherever the width came from. Write
  such a directive's name in prose rather than its bracket form -- a
  parser scanning for the form finds it in the sentence describing it,
  backticks and all
- The second is an unbreakable token: a bare URL, or a Markdown link an
  author does not break across lines. A line is exempt when such a token
  plus its indentation does not fit the width, since no wrapping
  shortens it. Measure the token, not the line with the token deleted:
  the second test excuses every long line that happens to carry a link.
  State the exemption in the check rather than leaving it a convention,
  or the rule grants an excuse the check reports anyway -- and a report
  whose one standing finding is the one everybody dismisses stops being
  read
- A project that declares no width has no rule, whatever its documents
  happen to look like. Near-total compliance kept by hand is the
  signature of an unwritten rule: it looks healthy and decays at the
  edges with nothing to notice
- Check — the command reads the configured width rather than assuming
  one, reports how many files it inspected, and prints nothing after
  that. A project with no width configured fails it, because an unstated
  width is the defect and not a gap to fill with a default. A count of
  zero is a failure too: the enumeration reads the index, so a document
  that is not staged yet is invisible to it. The exemption narrows the
  findings and never the corpus — every tracked file is still read, so a
  line held up only by an unbreakable token stops being reported while an
  over-long line of prose beside it does not:

  ```bash
  py - <<'EOF'
import json, pathlib, re, subprocess

# The width and its exemptions come from project configuration, never
# from this check. A project that declares no width fails here, because
# an unstated width is the defect, not a default to fill in.
width, source = None, None
skip_fenced, skip_tables, skip_headings = True, True, False
cfg = pathlib.Path(".markdownlint.json")
if cfg.exists():
    rule = json.loads(cfg.read_text(encoding="utf-8")).get("MD013")
    if isinstance(rule, dict):
        width = rule.get("line_length")
        skip_fenced = not rule.get("code_blocks", True)
        skip_tables = not rule.get("tables", True)
        skip_headings = not rule.get("headings", True)
        source = str(cfg)
if width is None:
    ec = pathlib.Path(".editorconfig")
    if ec.exists():
        section = None
        for line in ec.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
            elif section and "md" in section and line.startswith("max_line_length"):
                width = int(line.split("=")[1].strip())
                source = str(ec)
if width is None:
    print("no Markdown line width is configured; declare one")
    raise SystemExit(0)


def is_directive(text):
    """A single-line directive a parser reads whole, such as [ID: x]."""
    text = text.strip()
    return (text.startswith("[") and text.endswith("]")
            and ":" in text.split("]")[0])


# The two tokens no wrapping shortens: a Markdown link, which an author
# does not break across lines, and a bare URL.
UNBREAKABLE = re.compile(r"!?\[[^\]]*\]\([^)\s]+\)|<?https?://[^\s>)]+>?")


def is_unwrappable(text, limit):
    """True where no wrapping brings the line under the limit.

    Measure the longest unbreakable token against the width, not the line
    with its tokens removed. The second test excuses any long line that
    merely contains a link, because deleting the link makes the rest fit;
    the first excuses only a line whose overflow survives every wrap.
    """
    indent = len(text) - len(text.lstrip())
    longest = max((len(m.group()) for m in UNBREAKABLE.finditer(text)),
                  default=0)
    return indent + longest > limit


tracked = subprocess.run(["git", "ls-files", "*.md"], capture_output=True,
                         text=True).stdout.split()
# git ls-files reads the index, so a document not yet staged is invisible
# here and the assertion passes having never seen it.
print("markdown files inspected: %d" % len(tracked))
if not tracked:
    print("no tracked Markdown found; the enumeration is broken, "
          "not the tree clean")
for name in tracked:
    fenced = False
    for number, line in enumerate(
            pathlib.Path(name).read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced and skip_fenced:
            continue
        if skip_tables and line.lstrip().startswith("|"):
            continue
        if skip_headings and line.lstrip().startswith("#"):
            continue
        if is_directive(line):
            continue
        if len(line) > width and not is_unwrappable(line, width):
            print("%s:%d %d > %d (%s)" % (name, number, len(line), width, source))
  EOF
  ```

- Write in present tense — past or future tense indicates out-of-sync
  documentation
- Write as little as necessary but as much as needed — documentation that goes
  out of sync is worse than no documentation
- Remove redundant, inconsistent, or outdated documentation promptly
- Use full, grammatically correct sentences — enumerations are exempt
- Use bold and italic sparingly — never bold inline code or a whole sentence,
  and use at most one short bold label per list item
- Code-format only identifiers (file names, paths, env vars); summarize whole
  commands and flags in prose rather than transcribing them as inline code
- Summarize intent and link to the source — do not transcribe methods,
  constants, or flags into prose
- The same holds for a self-documenting source. A hand-maintained table
  restating a CLI's `--help`, a generated schema, or generated API docs
  is a second copy that drifts the moment someone adds an option and
  forgets the table, leaving readers trusting a list that is quietly
  wrong. Point at the command or the generated artifact instead, and
  document only what it cannot state itself — why an option exists,
  which combinations are meaningful

## Diagrams and assets

- Prefer text-based diagram formats: Mermaid for flowcharts, sequence diagrams,
  and Gantt charts; Draw.io for complex visual diagrams
- Commit all raw editable sources alongside rendered outputs
- An artefact committed as a hand-editable source has exactly one
  authority. Where a generator produced it, the generator is scaffolding
  and is NOT committed — otherwise the tree holds two authorities for one
  artefact, whoever opens the editor and moves a box has their work
  silently reverted by the next run, and nothing in the tree says which
  of the two is current
- Committing the generator instead is equally coherent, but then the
  artefact is build output and MUST NOT be described or edited as a
  source. Either choice is fine; having both in the tree is the defect
- Do not use proprietary formats (Word, Illustrator, Affinity Designer)
- Diagrams MUST be version-controlled — binary-only diagrams are not acceptable
- Use uniform node shapes; split a diagram that serves two purposes (e.g.
  happy path vs error path, or build vs runtime)
- In Mermaid notes, avoid `;` (a statement separator) and a bare `<` (opens a
  tag inside `<br/>` notes) — both silently break rendering

## arc42 architecture documentation (if applicable)

[ID: docs-arc42]

For projects documenting architecture with arc42, these conventions keep
chapters consistent and prevent the common cross-section leaks. The
general writing-style and diagram rules above still apply.

### Chapter boundaries

- **§2 Constraints vs §4 Solution Strategy** — §2 holds only *givens*
  (language, OS/platform, environment and resource limits, licensing,
  process and tooling). Technology *selections* (frameworks, libraries,
  servers, algorithms, protocols, patterns) are §4 decisions, not §2
  constraints. Tell: a "constraint" carrying a justification ("…because
  X is hard") is a decision
- §2 constraints are forward-stated — never reverse-engineered from
  code; no file/line citations and no "source" column
- §3 Context stays high-level — no source-file paths, tool names, or
  registry/platform names (those live in §7/§9). §3.2 technical-context
  channels are external partners only — an in-process library is not a
  channel. §3.3 "In scope" lists project deliverables, not a re-list of
  the §1 functional requirements
- §3 diagrams are black-box — use the arc42 partner / input / output
  table and distinguish human actors from systems
- §5 building blocks are named for the role each plays, and the chapter
  states where each role meets the tree — an `Implementation` column on
  the level 1 table, or the identifier beside each level 2 heading.
  Without it the mapping exists only in the head of whoever wrote the
  chapter, and the chapter passes review because it is internally
  coherent: nothing in it is wrong, it simply does not join to the tree
  it describes
- That is the §8 concept-to-identifier mapping applied to §5. The §3
  rule against source-file paths above is scoped to context, and that
  scoping is what puts the mapping on the §5 side of the boundary
- Where a block name and its implementation use different words, §5 says
  why, so a deliberate distinction is not read as an oversight. Tell: a
  block name that is also a real identifier defined elsewhere in the
  chapter, with nothing telling the two apart
- Chapters cite no ADRs — keep inline `AD-N` citations and generic
  "ADR" / "decision record" mentions out of chapter bodies; §9 is the
  single ADR index

### IDs and register

- Functional requirements use `FR01…` in shall-form (IEEE 29148);
  quality goals use `QG01…` named for a characteristic of ISO 25010,
  distinct from the `Q1…` quality scenarios in §10
- Name the ISO 25010 edition the goals are drawn from, because the
  characteristic set changed between them and a goal named for a retired
  characteristic cannot be found in the standard it cites. ISO/IEC
  25010:2023 has nine: Functional Suitability, Performance Efficiency,
  Compatibility, Interaction Capability, Reliability, Security,
  Maintainability, Flexibility and Safety. Usability and Portability are
  2011 names retired into Interaction Capability and Flexibility; Safety
  is new in 2023
- Name a sub-characteristic where it is more precise — Functional
  Correctness, Functional Completeness, Availability. "Correctness"
  unqualified is in no edition; the characteristic it belongs to is
  Functional Suitability
- The `QG0n` id is the join key across §1, §4 and §10 — §4's
  quality-approach table and §10's scenario table both carry it, so a
  script can assert the three still agree
- Requirements use "shall"; constraints and other givens stay
  declarative — avoid all-caps RFC 2119 keywords in arc42 prose
- A per-section purpose line only where it adds meaning (define a term
  or draw a distinction such as FR vs NFR) — never restate the heading
- No forward cross-references to later-numbered sections (a section is
  authored before they exist); back-references are fine

### Requirement and goal content

- A quality goal states how well the system behaves, never what it
  does. Tell: the clause appears verbatim as an `FR` row in the same
  chapter — that is a duplicate, not a goal
- A quality goal is not the product's purpose restated. Tell: the
  motivation reads "…is the reason the service exists"
- A statement a single observation can confirm is a requirement, not a
  quality goal. A goal is a universal that no one case settles, a measure
  of what something costs, or a property of the source rather than of the
  running system
- The quantifier is what separates the two, so it is visible in the
  phrasing: "every broken internal link is found" is a goal, "a broken
  internal link is found" is the requirement underneath it. Tell: a goal
  that reads as two FRs conjoined, or that restates constraints already
  in §2, is a requirement wearing a category label
- Security goals state who may do what; the mechanism that enforces it
  (bind address, reverse proxy, allowlist) belongs in §2 or §4. Tell: a
  goal the system's own top security risk cannot violate
- Every quality goal carries its measurable target in §1 — a figure
  living only in a §10 scenario leaves §1 unfalsifiable
- One goal covers one quality with one failure mode — split a goal
  whose clauses can fail independently of each other
- Goal coverage follows what the component is, not only what its risk
  register lists: a component inline on a write path declares
  efficiency, a component with human users declares usability
- A motivation gives a fact and the consequence that follows from it —
  a bare fact does not justify a priority
- §10 scenarios are falsifiable — a scenario naming module counts, file
  layout, or bind addresses describes what was built and cannot fail
- §10 is one table, not a table plus a quality tree — a tree duplicates
  the scenarios at lower resolution and drifts from them; carry the ISO
  25010 sub-characteristic and the `QG0n` id as columns instead
- A §10 scenario known not to hold today says so in its expected
  response and cites the §11 entry — a scenario stating only the target
  reads as an aspiration
- Adding or renaming a quality updates three places: the §1 goal table,
  the §4 quality-approach table, and the §10 scenario table

### Concept sections

- Describe the idea in prose, then give a `Concept | Implementation`
  table mapping it to concrete identifiers — rather than inlining
  identifiers throughout the prose

### Risks and technical debt

- §11 holds two registers that are not interchangeable. A risk is a way
  the system can fail that has not happened, rated probability × impact.
  Technical debt is a weakness that exists now, rated impact × effort.
  Tell: an entry whose probability is `Certain` is not a risk — it is
  debt, or a limitation belonging in §1 scope
- The table rates, prose explains. A cell holds an id, a one-sentence
  statement and a rating, and nothing longer. An entry needing evidence,
  a trigger or a qualification gets a short subsection below the table
  keyed by its id. A table is a comparison device — two three-sentence
  cells cannot be read across, so the register stops comparing anything
- Register ids are `R01…` and `TD01…` — zero-padded, no separator,
  matching `FR01` and `QG01`
- Register ids are chapter-local: no other chapter cites one. This is
  the containment §9 already has for decision records, and it is what
  the no-forward-reference rule above breaks against when a §4 or §8
  body reaches into a register defined later
- An entry that outgrows the register becomes a decision record. When it
  needs alternatives, evidence, or reasoning that has to stay fixed, it
  is a decision, and §9 holds those — the entry leaves §11 rather than
  citing across, since chapters cite no ADRs. Without this boundary §11
  becomes a second decision directory, and a mutable one
- §11 carries its content while §9 only indexes, and that asymmetry is
  deliberate. A register is mutable state — a mitigated risk is deleted,
  a probability is edited in place — and a decision record is immutable.
  Applying either shape to the other destroys one of them, so neither is
  migrated for symmetry with the other
- An entry leaves the register when it is resolved. A mitigated risk is
  deleted, never annotated with a status column or moved to a Resolved
  heading; version control holds the history. The register is an
  inventory of what is wrong now
- A register entry states a weakness and schedules nothing. Where the
  remedy is work someone is expected to do, the row names its tracked
  home in the issue tracker. An entry with no tracked home is a standing
  weakness, and the register is then the only surface that will ever
  raise it again — which is a choice, and is made deliberately
- Check — every register id occurs in the chapter that defines it. Pass
  condition: the command reports how many register chapters it found and
  how many ids, then prints nothing after that. Zero ids means two
  different things and the two counts are what separate them: with no
  chapter declaring a register the project never adopted the convention
  and the check does not apply, which it reports with exit status 3 — the
  reserved status for a check answering that its question is not live
  here — while a declared chapter holding no ids is the convention having
  drifted. The register is opt-in, so its
  absence is not a finding — a check reporting drift against a
  convention a project never took up prints a defect that does not exist
  on every run, and a standing finding is one a reader learns to
  dismiss. Ids in use with no chapter declaring them is the third case,
  and each is listed:

  ```bash
  py - <<'EOF'
import pathlib, re
IDS = re.compile("(?<![A-Za-z0-9])(?:R|TD)[0-9]{2}(?![0-9])")
OWNS = re.compile("^#{1,3} .*(?:risk|technical debt)", re.I)
docs = sorted(pathlib.Path("docs").rglob("*.md"))
found, stray, owners = 0, [], []
for path in docs:
    lines = path.read_text(encoding="utf-8").splitlines()
    defines = any(OWNS.match(line) for line in lines)
    if defines:
        owners.append(path)
    for number, line in enumerate(lines, 1):
        for hit in IDS.findall(line):
            found += 1
            if not defines:
                stray.append("%s:%d cites %s outside the register"
                             % (path, number, hit))
print("register chapters found: %d in %d document(s)"
      % (len(owners), len(docs)))
print("register ids found: %d" % found)
if not owners and not found:
    print("no register chapter is declared and no ids are in use; "
          "this check does not apply")
    raise SystemExit(3)
elif not owners:
    print("ids are in use but no document declares a register chapter")
elif not found:
    print("a register chapter is declared but holds no ids; the id "
          "convention drifted")
for line in stray:
    print(line)
  EOF
  ```

### Glossary

- Every glossary term is bold — `**term**`, never inline-code
  monospaced, and never left as plain text. Applies to identifiers
  (table names, routes, service names) as much as to prose terms
- The definition following the term is plain text

## Docs-as-code

- Technical documentation lives in the repository alongside the code
- Documentation follows the same review process as code
- All documentation MUST be written in Markdown

## Citing the software (if applicable)

Where the project expects to be cited, the citation of record MUST be a
persistent identifier, not a URL. A repository URL or project domain can
move, lapse, or be rebranded, and rots every citation pointing at it; a
persistent identifier resolves to an archived, immutable snapshot and is
independent of any website, so the domain stays freely swappable.

- SHOULD archive each release and mint a persistent identifier, then
  cite the identifier that resolves to the latest version rather than a
  per-version one
- SHOULD ship a machine-readable citation file at the repository root so
  the forge renders a "cite this repository" affordance, and record the
  identifier in it
- A project domain or vanity URL is a convenience for readers and MUST
  NOT be presented as the citation of record

## Generated files

Files committed to the repository but produced by a tool (rendered
docs, generated configs, resolved template chains, code-from-schema
output) rot in four predictable ways: maintainers hand-edit them,
the source changes but the committed output is not refreshed, a
formatter touches the file at commit time and a later check flags
it as stale, or the output is produced with a different invocation
than the documented one.

- The fourth mode is the one that defeats review. The file is not
  stale, not hand-edited and not reformatted — it is simply generated
  differently, and for a visual or binary output the property that
  differs is usually not one the artifact displays. An export committed
  at half the documented scale renders every arrow correctly, and the
  smaller file reads in the diffstat as a compression win, so every
  signal available to a reviewer points the wrong way. The staleness
  gate MUST re-render rather than rely on inspection
- Committed diagram exports are the common instance. A rendered `.png`
  beside its editable source is a generated file by the definition
  above, but it reads as an asset, so a project can apply `--check`
  faithfully to its config and schema output and never think to point
  it at `docs/assets/`
- Every generated file SHOULD start with a banner identifying the
  tool that produced it and the command to refresh it. Example:

  ```markdown
  <!-- Generated by `py tools/generator.py`. Edit the source
       (path/to/source.yaml) or the renderer, not this file. Run
       `py tools/generator.py --check` to verify the committed
       file is up to date. -->
  ```

- Every generator SHOULD expose a `--check` flag that re-renders
  in memory and exits non-zero on diff or missing file. This is
  the CI-staleness gate; wire it into pre-commit and CI as a
  required check
- Formatters (Prettier, Black, gofmt, etc.) SHOULD ignore generated
  paths — otherwise the formatter reformats the file at commit time
  and `--check` then reports a confusing stale-file failure on the
  next run
- When a generated file's inputs change (a rename, move, or schema
  bump), re-run the generator rather than string-editing the artifact
  — the banner's "do not edit" header is a contract, and the next
  `--check` run flags a hand-edited file as stale against freshly
  generated content
- The `--check` rule applies whether the script renders one file or
  rewrites many entries inside one source-of-truth file. A bulk-emit
  script that mutates multiple slugs / entries / records in a single
  file MUST support `--check` and be wired into CI as a required gate
  — otherwise extractor drift accumulates silently and surfaces as a
  multi-hundred-line diff during an unrelated, narrow PR
- A bulk-emit `--check` failure MUST report the count of stale entries,
  not just the file path. "19 of 19 entries stale" tells the maintainer
  the extractor itself drifted; a bare filename reads like a one-line
  edit and hides the scale
- A generator that renders per-field output (report columns, table
  sections, config stanzas) MUST derive the field enumeration from the
  data schema it renders, never from a hardcoded list. A fixed list
  fails both ways at once: it renders dead columns for fields the data
  lacks, and silently omits fields it has — and the omission hides
  exactly the records the artifact exists to surface. The dead columns
  are the visible tell; treat them as a defect, not cosmetics
- A round-trip generated file — one the generator scaffolds and then
  refreshes in place while preserving human-owned edits (annotation
  files, mark-up review tables, scaffolded configs with user sections)
  — MUST on refresh either preserve human-entered content or fail loud
  naming what it would discard. Silently reverting an edit that does not
  match the preservation convention (an unmarked cell) is data loss even
  when documented. Two compliant behaviours: treat divergent unmarked
  content as a correction to keep, or refuse the refresh naming the cell

## Output file by agent

| Agent            | Context file                      |
| ---------------- | --------------------------------- |
| Claude Code      | `CLAUDE.md`                       |
| Cursor           | `.cursor/rules/project.mdc`       |
| GitHub Copilot   | `.github/copilot-instructions.md` |
| OpenAI Codex CLI | `AGENTS.md`                       |
| Generic / other  | `AI_CONTEXT.md`                   |
