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
- ADRs are immutable once merged — create a new ADR to supersede an old one
- A content-preserving format migration preserves immutability and needs
  no superseding ADR: normalizing headings, titles, filenames, or
  cross-links across merged ADRs is allowed as long as it changes no
  decision prose (Context, Decision, Alternatives considered,
  Consequences). The commit MUST state "format-only, no decision
  change". Changing a decision's substance still requires a new ADR
- When an ADR's premise is refuted shortly after it merges (typically by
  data that should have informed it), prefer a same-day or same-week
  supersession ADR documenting the post-mortem over silently closing the
  follow-up issues — an `Accepted` ADR describing code that does not exist
  is documentation-vs-code drift. The supersession ADR records the refuting
  evidence and a post-mortem (Symptom / Root cause / Why missed / Fix /
  Prevention) if the original shipped any change; the superseded ADR's
  status flips to `Superseded by ADR-NNN` in the same PR
- File naming: `NNN-slug.md` — zero-padded sequence number + kebab-case slug
  (e.g. `001-data-storage.md`, `002-hosting.md`)
- ADR file format:

```markdown
# ADR-NNN: [Decision title]

**Status:** Accepted | Superseded by ADR-NNN
**Date:** YYYY-MM-DD

## Context

[Why this decision was needed]

## Decision

[What was decided]

## Alternatives considered

[What was rejected and why]

## Consequences

[What follows from this decision]
```

- Do NOT maintain a monolithic architecture document that mixes decisions,
  data model specs, and migration tracking — decisions go in ADRs, data
  model is the code (`src/types/`), migration tracking belongs in the
  dev journal or issue tracker
- ADRs MUST NOT reference future ADRs that do not exist yet — reference
  backward only; each ADR is self-contained at the time of writing
- Implementation details (phrase tables, templates, worked examples) belong
  in the ADR itself, not in separate spec files — external specs create
  maintenance burden and go stale
- Non-trivial ADRs SHOULD include at least one inline ASCII diagram or
  mockup in the Decision section — a pipeline flow, layout sketch,
  state transition, or similar — so the concept is scannable without
  parsing dense prose. Use plain ASCII (`+`, `-`, `|`), not Unicode
  box-drawing characters, to stay consistent with the ASCII-only
  source-content rule and keep diffs clean. Example:

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
  quality goals use `QG01…` with ISO 25010 names (Correctness,
  Reliability, Maintainability, Portability, Compatibility, Usability) —
  distinct from the `Q1…` quality scenarios in §10
- Requirements use "shall"; constraints and other givens stay
  declarative — avoid all-caps RFC 2119 keywords in arc42 prose
- A per-section purpose line only where it adds meaning (define a term
  or draw a distinction such as FR vs NFR) — never restate the heading
- No forward cross-references to later-numbered sections (a section is
  authored before they exist); back-references are fine

### Concept sections

- Describe the idea in prose, then give a `Concept | Implementation`
  table mapping it to concrete identifiers — rather than inlining
  identifiers throughout the prose
- A glossary entry is a **bold term** followed by plain text — no
  inline-code monospacing of the term

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
