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

Guide-doc filenames follow a deliberate casing split: single-word guide
docs use SHOUT-case (`README.md`, `CLAUDE.md`, `ONBOARDING.md`,
`PLAYBOOK.md`, `SPEC.md`); multi-word descriptive docs use lower
kebab-case (`dev-journal.md`). This is intentional, not drift.

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
  to an ADR that does not exist yet cannot be written at all
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
journal session entry. Format:

- **Symptom:** what the user saw
- **Root cause:** what was actually wrong
- **Why missed:** what review or test gap allowed it
- **Fix:** PR reference
- **Prevention:** what was changed to catch it next time

Not needed for minor fixes or cosmetic bugs. The purpose is to produce
actionable prevention steps — a post-mortem without a prevention action
is incomplete.

## Writing style

- Markdown wraps at the width the project declares in configuration,
  never at a width written into a rule. A document is not code and
  does not inherit the source line limit; it gets its own, and the
  project chooses the number
- Declare the width ONCE — in the Markdown linter's configuration or
  in `.editorconfig` under the Markdown section, not both. A second
  copy drifts from the first and nothing says which one won
- The exemptions travel with the declaration. Which of fenced blocks,
  table rows, headings and unbreakable link targets are excused is
  part of the configured rule, not a convention each author infers
- One exemption is structural rather than configured, because the
  line cannot be wrapped at all: a bracketed single-line directive a
  parser reads whole, such as a template's dependency header.
  Wrapping it changes what it means, so the check skips it wherever
  the width came from. Write such a directive's name in prose rather
  than its bracket form -- a parser scanning for the form finds it in
  the sentence describing it, backticks and all
- A project that declares no width has no rule, whatever its documents
  happen to look like. Near-total compliance kept by hand is the
  signature of an unwritten rule: it looks healthy and decays at the
  edges with nothing to notice
- Check — the command reads the configured width rather than assuming
  one, reports how many files it inspected, and prints nothing after
  that. A project with no width configured fails it, because an unstated
  width is the defect and not a gap to fill with a default. A count of
  zero is a failure too: the enumeration reads the index, so a document
  that is not staged yet is invisible to it:

  ```bash
  py - <<'EOF'
import json, pathlib, subprocess

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
        if len(line) > width:
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
- Chapters cite no ADRs — keep inline `AD-N` citations and generic
  "ADR" / "decision record" mentions out of chapter bodies; §9 is the
  single ADR index

### IDs and register

- Functional requirements use `FR01…` in shall-form (IEEE 29148);
  quality goals use `QG01…` named for an ISO 25010 characteristic
  (Functional Suitability, Performance Efficiency, Compatibility,
  Usability, Reliability, Security, Maintainability, Portability) or for
  a sub-characteristic where that is more precise (Correctness,
  Functional Completeness, Availability) — distinct from the `Q1…`
  quality scenarios in §10
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
output) rot in three predictable ways: maintainers hand-edit them,
the source changes but the committed output is not refreshed, or a
formatter touches the file at commit time and a later check flags
it as stale.

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
