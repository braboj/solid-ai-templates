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
