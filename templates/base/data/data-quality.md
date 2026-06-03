# Base — Data Quality
[ID: base-data-quality]
[DEPENDS ON: templates/base/data/data-modeling.md]

Rules for projects where content or data accuracy matters as much as
code quality. Applies to lens databases, product catalogs, tutorial
content, wiki entries, and any project that declares data as a
first-class concern.

---

## Data sourcing
[ID: data-quality-sourcing]

- Every data point MUST trace to a named source (URL, publication,
  manufacturer spec sheet)
- Record the source alongside the data — not in a separate document
- Prefer primary sources (manufacturer, official docs) over aggregators
- When multiple sources conflict, document the conflict and the chosen
  value with rationale
- Never fabricate or estimate values without marking them as estimates

---

## Completeness tracking
[ID: data-quality-completeness]

- Define a completeness score for each entry: fields populated / total
  fields (e.g. `14/14`)
- Track completeness at the entry level, not just the collection level
- Incomplete entries MUST be queryable — add a `completeness` or
  `dataStatus` field
- Set a minimum completeness threshold for publishing (e.g. 80%)
- Entries below the threshold MAY exist in the database but MUST NOT
  appear in user-facing views

---

## Freshness
[ID: data-quality-freshness]

- Record when each entry was last verified: `lastVerified` date field
- Define a freshness window per collection (e.g. prices: 30 days,
  specs: 12 months)
- Entries beyond their freshness window SHOULD be flagged for review
- Price data MUST include a `priceDate` field — never show a price
  without indicating when it was captured
- Discontinued or unavailable items MUST be marked, not deleted

---

## Exact vs estimated values
[ID: data-quality-precision]

- Distinguish exact values (from specs or measurements) from estimates
  (derived, rounded, or interpolated)
- Use a naming convention or field suffix to mark estimates (e.g.
  `weightEstimated: true` or `~` prefix in display)
- Default to realistic/pessimistic estimates — never optimistic
- Document the estimation method when not obvious

---

## Calibration discipline
[ID: data-quality-calibration]

When a tool is calibrated against reference data (test fixtures with
known-correct outputs, benchmark expected results, eval data, decision
thresholds), three failure modes silently invalidate the calibration:
suspect data treated as ground truth, the threshold tuned to mask a
broken measurement, and reference values produced by the same actor
that runs the tool. The rules below address each.

### Ground truth comes from raw artifacts, not suspect data

- When calibrating a pipeline against existing committed data, verify
  the data was not produced by an earlier version of the same pipeline
- If it was, and the pipeline has known or suspected bugs, the
  committed data is NOT ground truth — calibrating against it bakes
  the existing bugs into the new gate
- Build the calibration set from raw artifacts (source images, raw
  exports, captured fixtures), recording the verified value alongside
  each entry
- A small hand-built reference set from raw artifacts beats a large
  set carried over from a suspect pipeline

### Thresholds move, not the measurement

- When a measurement and a threshold disagree, the threshold is the
  cheaper thing to change — but ONLY after the measurement is verified
  sound
- Order of operations on disagreement: (1) verify the measurement
  against an independent check, (2) tune the threshold if the
  measurement is sound, (3) change the measurement implementation
  ONLY when steps 1 and 2 fail to resolve the disagreement
- A threshold picked from theory and never validated against data is
  not a calibrated threshold — it is a guess; tuning it against the
  data on first disagreement just hides the original guess
- This rule applies wherever measurements meet thresholds: CI quality
  gates, performance budgets, ML decision boundaries, extractor
  agreement scores

### Reference data MUST carry provenance

- Each entry in a reference set MUST record `source: agent | user |
  external` (who produced the value) and `verified: true | false`
  (whether a human has reviewed it)
- An agent MAY produce reference values to speed calibration, but
  MUST set `source: agent` and `verified: false` until the user
  reviews — the user MAY veto, replace, or accept; accepting flips
  `verified: true`
- Calibration metrics computed against the reference set MUST report
  a coverage caveat alongside the headline numbers (e.g.
  "verified: 12/40"), so unverified reference data cannot silently
  dominate the metric
- Synthetic test inputs (faker-style data, generated fixtures) are
  out of scope — this rule covers reference *outputs* compared
  against tool *outputs*, not test inputs

---

## Cross-validation and tool trust
[ID: data-quality-cross-validation]

When stored data is cross-validated against an external source (vendor
page, API, spec sheet, scrape), two distinct failure modes produce
misleading divergence reports: a buggy validation tool that misreads
the source, and a semantic mismatch between *stored default* and
*source silence*. Both look like "the data is wrong" and waste
maintainer time on phantom fixes.

### Verify the tool before trusting its output

- When a validation, scraping, or migration tool drives a bulk data
  change, confirm the tool is correct BEFORE acting on its output
- A systematic tool bug masquerades as data divergence — applying
  the tool's values blindly corrupts correct stored data
- Treat a physically implausible output value as a tool defect:
  fix, re-run, then apply
- When the external source itself looks wrong (stale page, wrong
  record served), cross-check an independent source before
  overwriting stored data
- Applies to scrapers, importers, schema-migration verifiers, and
  lint-driven codemods — any automated diff that drives a bulk
  change

### Distinguish source-silent from source-says-false

- A stored default (e.g. `absent boolean = false`) and source
  silence (the source did not mention the field) are NOT the same
  thing — treating them as equivalent produces a flood of
  false-positive mismatches that bury real errors
- The extractor MUST return a field ONLY when the source
  affirmatively states it
- The differ MUST compare a field ONLY when present on both the
  stored and source sides — source-silence skips comparison, never
  becomes a confirmed value
- This keeps stored-default conventions (`absent = false`,
  `null = unknown`) intact while making cross-validation meaningful
- The trap is non-obvious: the stored-default convention and the
  verification semantics pull in opposite directions, and the naive
  implementation looks correct until run against real data

---

## Data research workflow
[ID: data-quality-research]

When data enters the system from external sources (official pages,
lab reviews, retailers, scraped documents, public APIs), the
research workflow itself can introduce systematic errors that
later validation cannot detect. The rules below cover gathering
facts from multiple sources of differing authority, auditing whole
records rather than spot fields, extracting figures from composite
images, and caching fetched content.

### Source-conflict resolution

- The most-authoritative source (official publisher, manufacturer
  spec sheet, primary documentation) wins on any contested field
- If a secondary source is provably wrong on one verifiable field,
  treat ALL its unverified fields for that record as suspect — it
  is likely mis-cataloged or mismatched. Do NOT cherry-pick its
  other figures
- Prefer leaving a field unresolved-and-flagged over overwriting it
  with a contradicted source — a known gap is more useful than a
  confidently-wrong value
- When two sources of equivalent authority disagree, record the
  conflict, the chosen value, and the rationale alongside the
  entry (see [ID: data-quality-sourcing])

### Full-record audit, not target-field audit

- When verifying a record against a source, cross-check EVERY
  field — not only the fields that prompted the verification
- Copy-derived records frequently inherit stale values in fields
  nobody re-checked (e.g. a "v2" entry retaining the v1 release
  date or dimensions)
- A spot-fix audit confirms the target field while leaving silent
  drift in the rest of the record; a full-record audit catches
  the drift

### Content-aware figure cropping

- When extracting a figure from a composite image (marketing
  layout, manual page, dashboard screenshot), detect the content
  bounding box programmatically — e.g. corner-median background
  subtraction — rather than hand-guessing crop coordinates
- Hand-picked coordinates silently truncate or off-center the
  artifact; the error is caught only by a human eyeballing the
  output
- Keep automated edge-touch checks advisory (a tight axis box or
  wide subject legitimately reaches the margin) and always have
  a human review the crop before publishing

### Cache validity: content checks, not blind TTL

- For a research-time fetch/scrape cache (NOT the live request
  path), decide cache validity by the content of a cached
  response, not its age
- Never cache non-content responses — bot/throttle interstitials,
  4xx/gone error pages, implausibly short stubs. Detect and skip
  them on write
- Self-heal on read: if a cached body is recognizably junk
  (bot/404/empty), ignore and re-fetch rather than re-serving the
  bad cache
- Refresh deliberately via an explicit `--no-cache` / force flag,
  NOT on a timer
- Add a time-based TTL only when there is evidence that content
  goes stale in a way the content checks do not catch — a timer
  cannot distinguish a value change from a resource removal (the
  latter surfaces as 4xx and is handled above), and it slows every
  session re-fetching unchanged data
- Live request-path caches (Cache-Control, CDN, browser cache)
  are out of scope — those have their own TTL semantics

---

## Scoring and derived fields
[ID: data-quality-scoring]

- Scoring formulas MUST be documented — not buried in code
- All inputs to a score MUST be traceable to source data
- Scores MUST be reproducible: same inputs always produce the same
  output
- Define the scoring scale once (e.g. 1–5, step 0.5) and use it
  consistently
- Features (boolean attributes like "weather sealed") are UI filter
  badges, not scoring inputs — keep them separate

---

## Data changelog
[ID: data-quality-changelog]

- Changes to source data MUST be committed with a message explaining
  what changed and why (e.g. "fix: update lens weight — manufacturer
  corrected spec sheet")
- When a scoring input changes, note that derived scores will change
- Do not batch unrelated data changes into a single commit — one
  entry or one field correction per commit
- For bulk imports or migrations, document the source and method in
  the commit message

---

## Identity and deduplication
[ID: data-quality-identity]

- Every entry MUST have a stable unique identifier that does not
  change when other fields are updated
- Define what makes two entries "the same" — document the identity
  key (e.g. manufacturer + model name + variant)
- Near-duplicates (regional names, revised versions, bundles) MUST
  be distinct entries with a relationship field linking them
- Never merge near-duplicates silently — flag for manual review
- Discontinued items that are replaced by a successor SHOULD link
  to the successor via a `replacedBy` field

---

## Validation
[ID: data-quality-validation]

- Validate data at ingest time — reject or flag entries that fail
  schema validation
- Use typed schemas (Zod, JSON Schema, TypeScript interfaces) for all
  data collections
- Range checks for numeric fields (e.g. weight > 0, price > 0)
- Enum checks for constrained fields (e.g. mount type, category)
- Build-time validation is acceptable for static sites — runtime
  validation for APIs
