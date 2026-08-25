# Base — README
[ID: base-readme]

## Principle
A README is the front door of a repository. It MUST answer the three
questions a new reader asks within the first 30 seconds:
what is this, why does it exist, and how do I start using it.

## Required sections

Every README MUST contain the following sections, in this order:

### 1. Title and summary
- The repository name MUST appear as a top-level heading
- A badges line SHOULD sit directly under that heading — build
  status, latest version, license. Badges belong above the prose,
  where readers and every README in the wild expect them
- 2–4 sentences MUST follow the title: what the project does, for whom,
  what problem it solves, and why this solution exists — no preamble, no
  marketing language
- The summary block SHOULD follow a hook → problem → solution
  micro-structure:
  - **Hook paragraph** — 1–2 sentences naming a problem the reader
    already recognizes, before introducing the product
  - **Problem paragraph** — 1–3 sentences identifying the specific
    gap this project fills
  - **Solution paragraph** — 1–2 sentences describing what the
    project is
  - The four content fields (what, for whom, problem, why) MAY be
    distributed across these paragraphs in any way that reads
    cleanly. The hook is framing, not marketing — the existing
    no-marketing rule still applies
- An italic differentiator subtitle MAY appear below the badges and
  above the hook, when the project has a one-line claim worth
  elevating. The order at the top of the file is heading, badges,
  subtitle, summary

### 2. Features
- A capability list MUST follow the summary, under its own `## Features`
  heading (or a named equivalent such as `## Capabilities`) — bullet
  points stating what the product can do, written as capabilities not
  counts (e.g. "browse and filter products by spec" not "240+
  products"); this list is the product's contract and the primary input
  for value evaluation
- The heading is REQUIRED, not optional. Without one the bullets run on
  from the lede and the reader cannot tell where the prose ends and the
  contract begins

### 3. Quick start
- MUST be copy-pasteable: a reader MUST be able to go from zero to running
  in under five minutes by following this section alone
- Prerequisites MUST be listed before the first command
- Every command MUST be shown in a fenced code block with the shell indicated
- MUST NOT assume environment-specific context (paths, credentials, ports)
  without stating them explicitly

### 4. Usage
- MUST show the most common real-world usage — not every option, not
  contrived examples
- Each example MUST include the expected output or outcome
- If the project has multiple usage modes, each MUST have its own example

### 5. Project structure
- MUST map the directory structure covering the top two levels
- Each entry MUST have a one-line description of its purpose
- MAY be rendered as an indented directory tree or as a two-column
  table (`Path` | `Purpose`) — a table renders consistently on GitHub
  and structurally enforces the one-line-description rule
- Generated directories (`dist/`, `__pycache__/`, `.venv/`) MUST be omitted
- When the project ships an `examples/` directory, that directory MUST
  carry its own `README.md`, because the index is a README and this
  template owns those. What the index and the examples themselves MUST
  contain is `base-examples`, and MUST NOT be restated here

### 6. Development setup
- MUST cover: cloning, installing dependencies, running tests, running the
  application locally
- MUST list every external tool or service required (database, message
  broker, etc.) and how to start it
- If a `.env.example` file exists, MUST reference it here

### 7. Configuration reference
- SHOULD list every environment variable or configuration key the project
  reads, with type, default value, and a one-line description
- Sensitive keys (secrets, tokens) MUST be noted as such — never show
  real values as defaults

### 8. Links
- SHOULD link to: full API / library reference, CHANGELOG, contribution
  guide, and any deployed environments (staging, docs site)
- Internal links MUST use relative paths — not absolute URLs pointing to
  a specific branch or host

### 9. License
- MUST state the license name and include a link to the full license text
- MUST appear as the last section

## Rules

### Accuracy
- Every command MUST be tested and known to work at the time of writing
- A README that describes functionality not yet implemented MUST mark that
  section with a `> Note: planned for vX.Y` callout
- README MUST be updated in the same commit that changes the behaviour it
  describes — a stale README is a defect
- A README MUST NOT state a measured value that changes without a
  corresponding edit — coverage percentages, test counts, byte sizes,
  timings. The rules above cover content that goes stale when someone
  edits it; these go stale when nobody does, so no gate catches them.
  Name the file that holds the value and let the reader read it there
  (`fail_under` in the tool config, a CI badge, a generated report)
- Where an example's output is genuinely useful, describe its shape
  rather than its exact value

### Length and tone
- Write in present tense — past or future tense signals out-of-sync content
- SHOULD NOT exceed what a reader needs to evaluate or use the project —
  move deep reference content to `docs/`
- Avoid superlatives and filler phrases ("easy", "simple", "just run") —
  describe what the project does, not how good it is

### Audience
- A README serves two audiences. The first four sections (title,
  features, quick start, usage) are user-facing — what the product
  does and how to use it. The remaining sections (structure, setup,
  config) are developer-facing — how to build and contribute. Write
  each section for its audience.
- A README MUST NOT cite an individual decision record. The two
  audiences above are users and contributors; a decision record serves
  whoever maintains the decision. Link the document that explains the
  behaviour and let that document cite the record. The decisions
  directory MAY still appear in Project structure, which maps the tree
- Write for a reader who has not seen this project before — MUST
  NOT assume familiarity with internal terminology
- Acronyms MUST be expanded on first use

### Maintenance
- When a dependency version, command, or configuration key changes, the
  README MUST be updated in the same PR
- Sections that have not been updated in over six months SHOULD be reviewed
  for accuracy
