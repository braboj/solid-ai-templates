# Dev Journal

## 2026-06-24 — v2.10 data-quality finish & generator discipline

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Closed v2.10 — Data-quality finish (8/8 issues) across four
  theme PRs
- #424 split: moved **calibration discipline** and
  **cross-validation / tool-trust** out of `base-data-quality` into
  core `base-quality` so they reach all 30 stacks; the
  **data-research workflow** and data-schema rules stay in
  `base-data-quality` (opt-in via #298). ADR-013 records the split
  and supersedes ADR-012
- #431 + #443: added **diagnose-before-tuning** and **calibration
  aids must not depict the system's own output** as subsections of
  the now-core Calibration discipline section in `base-quality`
- #434 + #435: **coverage-by-cohort** data-validation pattern in
  `base-testing`; **fail-loud over auto-derivation** near Fail Fast
  in `base-quality`
- #437 + #444 + #445: generator-discipline trio — regenerate on
  input change (`base-docs`), regenerate derived artifacts in the
  fixing PR (`base-git`), and a new **Generated-file staleness
  gate** section in `base-quality-gates` making the `--check`
  invocation a required CI check
- Triaged the 72 then-unmilestoned issues into Backlog at the start
  of the session (Backlog 30 → 102)

**Lesson:** #424's stated premise — "agent-behavior rules reach all
stacks via `base-ai-workflow`" — was refuted on inspection:
`base-ai-workflow` is not in the core tier and no stack declares it,
so it reaches zero generated chains. Moving the rules there would
have *regressed* reach (they currently reach the Python-service
chain via ADR-012). Verify a rule's actual reach (core tier vs
opt-in) before choosing its home; core `base-quality` was the only
placement that satisfies "reach all stacks." The same correction
applied to #431's suggested `ai-workflow.md` home.

**PRs merged:** #534, #535, #536, #537

**Issues closed:** #424, #431, #434, #435, #437, #443, #444, #445

**Milestone:** v2.10 — Data-quality finish (8/8 closed)

---

## 2026-06-03 (evening) — v2.9.0 cut

**Tool:** Claude Code (Opus 4.7, 1M context)

**Key changes:**
- Closed v2.9's only open issue (#418): wired `base-data-quality`
  into `stack-python-service`, propagating transitively to Flask,
  FastAPI, and Django generated chains. Resolves the v2.8
  discoverability gap (`data-quality.md` rules now reach
  `generated/<stack>.md` for Python service stacks)
- Wrote ADR-012 bounding scope to python-service only; other
  backend stacks (Go, Node, Java, Celery) remain unwired pending
  the file-split decision
- Filed #424 as follow-up: audit `data-quality.md` and separate
  agent-behavior rules (calibration, cross-validation, research)
  from true data-heavy schema rules. The file's name overstates
  the data framing — three of four sections apply to any
  investigative work
- Cut v2.9.0: tag pushed, GitHub Release created, milestone closed

**Lesson:** when a base/ file's content is broader than its layer
suggests, wiring it forces a choice between leaving rules
unreachable or pulling unrelated dependencies. Better to question
the file's home (split or rename) than to over-wire — captured
as #424 follow-up

**PRs merged:** #425

**Issues closed:** #418

**Release:** v2.9.0 (https://github.com/braboj/solid-ai-templates/releases/tag/v2.9.0)

---

## 2026-06-03 (afternoon) — Expedite lane + milestone hygiene

**Tool:** Claude Code (Opus 4.7, 1M context)

**Key changes:**
- Created **Expedite** milestone (#15) — rolling fast-track lane for
  bugs, incidents, and small tasks shipping between versioned
  releases. Never closes; issues move in when expedited and out when
  shipped
- Codified Expedite in `templates/platform/github.md` Issue labels
  section (PR #420, closes #419), and extended the milestone-required
  rule from "every issue" to "every issue and pull request" with
  guidance that PRs SHOULD inherit the milestone of the issue they
  close
- Added per-folder-commit guidance to `base/core/git.md` Squash-merge
  safety section (PR #417, closes #409): prefer one focused commit
  per scope-slice over per-folder atomic commits — the squash
  collapses them, document the breakdown in the PR description
- Created **v2.9** milestone (#14) — "Data discoverability & gap
  fixes". Holds #418 (wire `base/data/data-quality.md` into stack
  DEPENDS ON chains — addresses gap flagged in v2.8) plus #403
  (README hook→problem→solution micro-structure) which shipped
  this session
- Codified hook → problem → solution micro-structure in
  `base/core/readme.md` §1 (PR #421, closes #403): three paragraph
  beats with sentence counts, optional italic differentiator
  subtitle, coexists with the four-content-fields rule
- Reassigned three closed issues from Backlog to their actual
  release milestones: #327 → v2.6, #138 → v2.5, #133 → v2.5. Five
  triage-only closures (1 duplicate, 4 wontdo) left in Backlog
  since no work shipped

**Lesson:** missed assigning PRs #417 and #420 to the Expedite
milestone at creation — rule said "every issue" but didn't cover
PRs. Caught and codified in the same PR (#420) that documents
Expedite, so the rule now self-applies

**PRs merged:** #417, #420, #421

**Issues closed:** #403, #409, #419

**Issues filed:** #418 (v2.9), #419 (Expedite)

**Milestones created:** v2.9 (#14), Expedite (#15)

## 2026-06-03 — v2.8 data discipline & calibration

**Tool:** Claude Code (Opus 4.7, 1M context)

**Key changes:**
- Shipped v2.8 milestone (8 issues) — three new sections in
  `templates/base/data/data-quality.md` plus one in
  `templates/base/workflow/quality-gates.md`
- Calibration discipline triad (PR #410, closes #344 / #346 / #381):
  ground truth from raw artifacts, thresholds move not the
  measurement, reference data provenance (`source: agent|user|external`
  + `verified: true|false` + coverage caveat in metrics).
  #381 redrafted from prohibition to provenance approach after
  discussion — preserves agent-eye-read speed while keeping user
  as judge
- Cross-validation and tool trust pair (PR #411, closes #333 / #335):
  verify the tool before trusting its output; distinguish source-
  silent from source-says-false
- Data research workflow pair (PR #412, closes #331 / #339):
  source-conflict resolution (authority + poison-pill), full-record
  audit, content-aware figure cropping, content-based cache validity
  (no blind TTL)
- Gate scope agreement (PR #413, closes #334): ignore lists and CI
  path-filter must agree, skipped is not passed, PR gate mirrors
  deploy gate. Closes the gate-by-omission anti-pattern
- Filed two backlog spikes: #414 (skills as UX layer on top of
  templates) and #415 (name-collision strategy for skills + slash
  commands). Sellability discussed and deferred — skills land free
  first, paid layer only after adoption data justifies it

**Gap flagged for follow-up:** `base/data/data-quality.md` is not
in any stack's `[DEPENDS ON]` chain, so the new data rules are
discoverable in the base layer but don't reach any
`generated/<stack>.md`. Candidate for v2.9.

**PRs merged:** #410, #411, #412, #413

**Issues closed:** #331, #333, #334, #335, #339, #344, #346, #381

**Issues filed:** #414 (spike), #415 (spike)

## 2026-06-02 — README clarify + dogfood generated-file convention

**Tool:** Claude Code (Opus 4.7, 1M context)

**Key changes:**
- README "How to use" section reworked: section 1 is now the
  fastest path (clone + tell the agent to read
  `templates/manifest.yaml`, agent picks the stack and follows
  `[DEPENDS ON]` itself). Sections 1 and 2 lead with a one-line
  "fastest / guided" contrast; stale "attaching a single file"
  comparison reworded; prerequisites narrowed to local coding
  agents; orphaned pre-resolved-file bullet dropped from Model
  limitations (PR #406)
- Dogfooded the generated-file banner + `--check` convention from
  PR #386: `tools/resolve.py` now prepends an identifying banner
  to every emitted file (banner names producing tool, refresh
  command, check command per `docs.md`). Wired both
  `py tools/sync.py --check` and `py tools/resolve.py --check`
  into `.github/workflows/smoke.yml`. Regenerating revealed weeks
  of silent drift in `generated/` (lines per file +200–300
  from earlier template additions never re-cached) — the new CI
  check would have caught it (#387, PR #407)

**PRs merged:** #406, #407

**Issues closed:** #387

## 2026-06-02 — v2.6 agent discipline & ADR governance

**Tool:** Claude Code (Opus 4.7, 1M context)

**Key changes:**
- Fixed SYS-02 smoke check to treat inline `[ID:]` references as
  references, not declarations — sole-line shape only. Routed
  SYS-02, TPL-04, TPL-06, TPL-07, TPL-08, TPL-09 through a shared
  `iter_id_declarations()` helper. Spec updated (#364, PR #383)
- Added close-and-resubmit pattern to `base/core/git.md` under
  Pull requests — codifies SHOULD close + new PR when branch /
  title / body no longer match the actual decision (#382, PR #384)
- Added Probe scripts subsection to `base/core/quality.md` under
  Debug code — throwaway investigation scripts (`probe_*.py`)
  MUST be deleted before commit; findings move to comments / ADRs
  / docs (#360, PR #385)
- Added Generated files section to `base/core/docs.md` between
  Docs-as-code and Output file by agent — banner + `--check` flag
  + formatter-ignore SHOULDs (#380, PR #386)
- Added Verify working directory before concluding on a negative
  rule to `base/workflow/ai-workflow.md` with
  `[ID: ai-workflow-pwd-on-negative]` — pwd check as first
  diagnostic step on unexpected negative path queries (#358, PR #388)
- Added inline-ASCII-diagram SHOULD rule for non-trivial ADRs to
  the Decision logs section of `base/core/docs.md` — plain ASCII
  (+/-/|), not Unicode box-drawing (#342, PR #389)
- Added Findings docs subsection to `base/core/docs.md` Decision
  logs — lightweight markdown co-located with data, distinguishing
  from ADRs (decisions) and dev journal (history) (#347, PR #390)
- Recorded ADR-010 ADR governance model + `docs/decisions/TEMPLATE.md`
  — YAML frontmatter (id, status, date, category, supersedes,
  superseded_by); closed status set (Proposed / Accepted /
  Superseded); closed category set (composition, templates,
  tooling, process, release); two-way supersession links as the
  ONE exception to immutability; flat-folder + status-filter
  archival; ADRs MUST NOT cite other ADRs in prose except via
  the frontmatter graph (#379, PR #394)

**Audit at session start:**
- Closed #304 as already done (RFC 2119 keywords already in
  `base/core/docs.md` Rule language table)
- Closed #327 as already done (wrap-up checklist in `scope.md`
  already enumerates steps 6 and 9 with "Name the section")
- Closed #328 as duplicate of #337 (newer, more concrete version
  of the docs/audits/ proposal)

**Triage:**
- 5 unmilestoned backlog issues moved to Backlog (#358, #360,
  #380, #381, #382) — none fit v3.0 restructure scope
- Created v2.6 milestone with 8 issues (Mixed: agent discipline
  + ADR governance + smoke bug)

**Follow-up issues created from session work:**
- #387 — Apply generated-file banner + --check to this repo's
  `generated/` files (dogfood ADR-010's convention)
- #391 — ADR migration: retrofit frontmatter onto ADRs 001-009
- #392 — Smoke check: enforce ADR frontmatter schema
- #393 — `CLAUDE.md` §2.9: summarize ADR governance, point to
  TEMPLATE.md

**Issues closed:** #304, #327, #328, #342, #347, #358, #360,
  #364, #379, #380, #382 (11 total — 8 v2.6 + 3 audit)

**PRs merged:** #383, #384, #385, #386, #388, #389, #390, #394

**v2.6 closeout: 8/8 done.**

---

## 2026-05-07 — v2.5 coverage and scope

**Tool:** Claude Code (Opus 4.6, 1M context)

**Key changes:**
- Mentioned codified industry standards in README overview (#210, PR #296)
- Added team consistency hook line to README intro
- Updated repo topics: removed generic (`templates`, `devtools`, `ai-tools`),
  added targeted (`12-factor`, `owasp`, `codex-cli`, `copilot`,
  `coding-standards`, `ai-workflow`, `code-quality`)
- Defined success metrics in imbra-explore IMCONTEXT.md section 09
  (#191, imbra-explore PR #45)
- Added 4 structural smoke checks: SYS-03 (manifest coverage),
  SYS-04 (header-manifest sync), TPL-08 (ID presence), TPL-09
  (section content) (#253, PR #300)
- Added section tag grammar, source of truth, and orthogonal
  templates sections to SPEC.md
- Proposed ADR-009: stack scope cap and fork-and-extend workflow

**Issues closed:** #191, #210, #253, #301, #302, #146, #147, #181, #182

**Issues created:**
- #297 — Add backend specialization templates to relevant stacks
- #298 — Add data-heavy stack template
- #299 — Spike: define orthogonality rules for core templates
- #301 — Sync DEPENDS ON headers with manifest depends_on (closed same session)
- #302 — Add missing [ID:] tag to ai-workflow.md (closed same session)
- #303 — Add smoke checks for heading structure and reachability
- #304 — Spike: apply RFC 2119 keyword discipline to SPEC.md
- #305 — Cap stack scope and define extension model

**PRs merged:** #296 (README), #300 (smoke checks + SPEC + ADR + fixes)

**Backlog cleanup:**
- Closed #146, #147, #181, #182 as wontdo per ADR-009
- Moved #13 to v3.0, converted to spike
- Moved #90 to Backlog
- Deleted v2.5 milestone

## 2026-05-06 — v2.4 milestone completion

**Tool:** Claude Code (Opus 4.6, 1M context)

**Key changes:**
- Closed #264 epic (audit generated stacks) — all 11 sub-issues done
- Created mobile layer: `templates/mobile/auth.md` and `mobile/ux.md` (#272)
- Refactored React Native/Flutter to use mobile layers instead of web templates
- Removed rule duplications across 11 stack templates (#275)
- Fixed dangling EXTEND references and terminology errors (#276)
- Added TPL-06 smoke check: chain reachability (#283)
- Added TPL-07 smoke check: duplication detection (#284)
- Added terminology review checklist to PLAYBOOK.md (#285)
- Restructured quality.md + added .editorconfig rule (#224, #255)
- Replaced stale hardcoded values in SPEC.md/PLAYBOOK.md (#203)
- Created ADR-008: issue and PR naming conventions (#233)
- Added focus-visible rule for anchor elements (#104)
- Closed #131 (Dependabot already present)
- Moved 5 new-content issues to Backlog

**PRs merged:** #282, #286, #287, #288, #289, #290, #291, #292, #293
**Issues closed:** #104, #131, #203, #224, #233, #255, #264, #272, #275, #276, #283, #284, #285
**Smoke checks:** 11 → 13 (TPL-06, TPL-07)

---

## 2026-05-06 — Template quality cleanup batch

**Tool:** Claude Code (Opus 4.6, 1M context)

**Key changes:**
- Fixed dependency chains: removed wrong deps (go-grpc, celery-worker,
  sveltekit), added missing deps across 9 templates (htmx, SPAs,
  nextjs, go-lib, java-grpc) — PR #278
- Split `base/core/quality.md`: extracted OOP into new
  `base/core/oop.md`, moved 12-factor to `backend/quality.md` — PR #279
- Cleaned framework-specific content from shared templates: testing.md,
  frontend/quality.md, frontend/ux.md, spa-react.md — PR #279
- Added 4 override declarations for stack contradictions (nestjs AOP,
  c-embedded testing, django statelessness, nextjs stack) — PR #280
- Merged 3 housekeeping PRs: Dependabot (#261, #262), dev journal (#263)
- Cleaned up stale branches (3 local + 40 remote refs pruned)

**Issues closed:** #265, #266, #267, #271, #273, #274, #277
**PRs merged:** #261, #262, #263, #278, #279, #280
**Epic updated:** #264 (8 of 11 sub-issues complete)

---

## 2026-05-06 — Generated stacks audit

- Tool: Claude Code (Opus 4.6)
- Audited 5 generated stacks: terraform, tutorial, python-lib, react-spa, go-service
- Created #264 (audit parent) + 4 sub-issues (#265–#268)
- Fixed #268: added `base-security` and `base-containers` to `backend-quality` deps — resolved missing dependency gap for all 6 service stacks
- Merged PR #269
- Swapped milestones: v2.4 is now Templates & Content, v2.5 is now Discovery

---

## 2026-05-06 — v2.3 Tooling milestone completion

**Tool:** Claude Code (Opus 4.6, 1M context)

**Key changes:**
- Added `.editorconfig` for consistent formatting (#184, PR #254)
- Added `.pre-commit-config.yaml` with trailing-whitespace,
  end-of-file-fixer, check-yaml, gitleaks hooks (#185, PR #256)
- Enabled Dependabot for pip and GitHub Actions (#186, PR #257)
- Added `eslint-plugin-sonarjs` to base/quality.md and 5 Node/TS
  stack templates with rule mapping table (#130, PR #258)
- Added lychee `--root-dir` rule to static site templates
  (#135, PR #259)
- Audited README, INTERVIEW, SPEC, PLAYBOOK for unsustainable
  generation claims — reframed templates as product (#242, PR #260)
- Created #255 (editorconfig recommendation for base/quality.md,
  assigned to v2.5)
- Closed v2.2 milestone, closed v2.3 milestone, released v2.3.0
- Removed descriptors from all release titles (v1.0.0–v2.2.0)

**Issues closed:** #184, #185, #186, #130, #135, #242
**Issues created:** #255
**PRs merged:** #254, #256, #257, #258, #259, #260
**Milestones closed:** v2.2 — Quality, v2.3 — Tooling
**Released:** v2.3.0

## 2026-04-27 — Skills roadmap

- Added Phase 15 (Skills) to `ROADMAP.md` with four categories:
  generative, transformation, review, ops — plus infrastructure tasks
- Renamed existing Phase 15 (Validation) to Phase 16
- Key insight: skills (dynamic, on-demand actions) complement static
  context files (CLAUDE.md/AGENTS.md) — they don't replace them

---

## 2026-04-28 — 360 analysis, labels, ADRs, license

**Tool:** Claude Code (Opus 4.6, 1M context)

**Key changes:**
- Created `base/360.md` — four-category project assessment template
  (Value, Quality, Viability, Discovery) with role prompts and parallel
  subagent execution model (19 sub-dimensions, 78 checklist items)
- Standardized issue labels to 12 canonical labels with Atlassian-style
  colors across 11 repos (10 Imbra-Ltd + braboj/tutorial-git)
- Split `base/issues.md` (platform-agnostic types) from
  `platform/github.md` (GitHub label implementation)
- Updated `base/readme.md` — capability list requirement, dual-audience
  clarification
- Created `docs/decisions/` with 3 ADRs: inheritance model, label
  standardization, 360 analysis
- Added CC BY 4.0 license (LICENSE file + README update)
- Documented bus factor mitigation in ONBOARDING.md
- Improved README: capability list, project structure, dev setup, links

**PRs merged:** #73, #74, #75, #76

**Issues closed:** #58 (duplicate), #66, #67, #68, #70, #71, #18

**Decisions:**
- ADR-001: Three-layer inheritance model (base → layer → stack)
- ADR-002: 12 canonical labels, Atlassian colors, type/priority split
- ADR-003: 360-degree analysis as parallel subagent evaluation
- License: CC BY 4.0 — maximizes adoption funnel, requires attribution
- Labels split: types in base/ (platform-agnostic), colors in platform/
  (GitHub-specific)
- Severity stays in bug body text, not as label — solo project, priority
  drives triage order

---

## 2026-04-30 — v1.0.0 release, repo transfer, CI hardening

**Tool:** Claude Code (Opus 4.6, 1M context)

**Key changes:**
- Tagged v1.0.0 release
- Transferred repo from Imbra-Ltd to braboj
- Added `base/quality.md` rule: never hardcode derived counts
- Added audit decomposition guidance to `base/review.md`
- Added SEO conventions to `frontend/static-site.md` and
  `stack/static-site-astro.md` (sitemap, description, JSON-LD)
- Fixed stale references in SPEC.md, ROADMAP.md, ONBOARDING.md,
  PLAYBOOK.md (CONCEPTS.md, format files, section ordering)
- Fixed e2e crash bug (3-tuple return on skipped tests)
- Added `base/360.md` to manifest.yaml
- Fixed test spec frontmatter ID mismatch
- Added `--offline` mode to e2e runner — validates test
  infrastructure without API calls
- Refactored test runners: extracted `tests/lib.py` (shared
  utilities) and `tests/cases.py` (30 test cases grouped by area)
- Added `--area` and `--fail-fast` flags to e2e runner
- CI hardened: enforce_admins, require PR before merge, gitleaks
  in smoke workflow, push protection enabled, e2e switched to
  offline mode in CI
- Updated label colors: task `#579DFF`, epic `#9F8FEF`
- Added 8 GitHub topics for discoverability
- Updated all in-repo URLs and submodule pointers after transfer

**PRs merged:** #80, #81, #91, #92, #93, #94, #95, #96, #97, #98, #99

**Issues closed:** #79, #78, #55, #15, #16, #82, #83, #84, #85,
#86, #87, #88, #89, #69, #72, #10

**Issues created:** #82–#90, #100

**Decisions:**
- Repo transferred to braboj for better OSS discoverability
- E2E CI runs offline mode — live mode is manual/nightly only
- gitleaks CLI preferred over gitleaks-action (no license key needed)
- Label colors updated for accessibility (task, epic were too dark)
- pytest adoption deferred — hand-rolled runners are sufficient

---

## 2026-05-01 — Session protocol hardening (superseded)

**Tool:** Claude Code (Opus 4.6, 1M context)

**PRs:** #120

**Issues closed:** #105, #106, #107, #110, #119

**Key changes:**
- Hardened `base/scope.md` session startup with branch check, git
  status, issue review, and mandatory startup block requirement
- Added build-after-change rule to during-work section
- End-of-session audit now requires visible sequential execution with
  documented trigger phrases
- `base/core/agents.md` — all three models (inline, reference, hybrid)
  now reference `base/scope.md` instead of inlining an incomplete
  6-step checklist
- Added `examples/hybrid-astro/CLAUDE.md` — first reference/hybrid
  mode example demonstrating the startup block pattern

**Key decisions:**
- Startup block is only required for reference/hybrid modes — inline
  models are self-contained and exempt
- Examples use anonymized fictional projects to avoid maintenance burden

---

## 2026-05-01 — Convention hardening sweep

**Tool:** Claude Code (Opus 4.6, 1M context)

**PRs:** #120, #121, #122, #123, #124

**Issues closed:** #105, #106, #107, #108, #109, #110, #111, #112,
#113, #114, #115, #116, #118, #119

**Key changes:**
- Session protocol: mandatory startup block, startup hygiene (branch/
  status/issues), build-after-change, visible sequential audit execution
- base/core/agents.md: all 3 models reference base/scope.md (no more
  incomplete inlined checklists)
- Quality: DRY/KISS/YAGNI core principles, Fail Fast/Law of Demeter/
  High Cohesion in maintainability, duplication erosion audit check
- Astro: View Transitions section with ClientRouter recommendation and
  DOMContentLoaded warning
- Docs: version bump in release process, session naming convention,
  milestone sync rule
- Added hybrid-mode example (examples/hybrid-astro/CLAUDE.md)
- Clarified extraction threshold: substantial logic blocks vs short
  inline repetition

**Also:** fixed 3 issue titles (removed commit-style prefixes), added
missing priority labels to #104, #105, #106

---

## 2026-05-04 — Composition over inheritance

Issues closed: #151, #149, #150
Issues created: #154 (implementation), #155 (repo org spike)

Three architecture spikes resolved in a single session. All decisions
recorded in ADR-004.

**#151 — Composition over inheritance (P1):**
- quality-gates.md depends on devsecops + cicd but never references
  their content — ISP violation. Remove both from depends_on.
- Core tier (5 files: quality, git, docs, readme, testing) always loaded.
  Manifest gets a top-level `core:` list.
- Stacks compose opt-in tiers explicitly — no transitive surprises.
- Stack classification: deployed services need devsecops + cicd; static
  sites, libraries, and mobile do not.
- Platform templates are facades — platform-github does not depend on
  devsecops.
- File headers must match manifest (direct deps only). 3 stale headers
  found: astro, hugo, tutorial.

**#149 — Pattern file integration (P2):**
- Evaluated 4 options (forward ref, manifest includes, auto-convention,
  resolution depth). All add complexity to the resolution algorithm.
- Deeper question: do agents need pattern tutorials? No — LLMs know
  standard patterns from training data. Agent context needs conventions,
  not recipes.
- Decision: remove all 5 pattern files from manifest and dependency
  graph. Move to docs/patterns/ as human reference. Parent rules files
  keep one-line summaries.

**#150 — Agent-side dependency resolution (P2):**
- Resolution algorithm: core → stack deps → extras → platform. All
  steps use RESOLVE_DEPS (recursive). Extras are recursive for safety.
- Algorithm runs at build time (tools/sync.py, interview), not at agent
  startup. Generates explicit file lists for CLAUDE.md startup blocks.
- Full IDs everywhere — explicit over implicit.

**Decisions (all in ADR-004):**
- ADR-004: Composition over inheritance in dependency model
- Manifest `core:` field for core tier
- Pattern files removed from dependency graph (~1700 lines saved)
- Build-time resolution, not runtime
- No profiles, no auto-convention, no pattern resolution logic

---

## 2026-05-04 — Pattern templates and quick wins batch

**Tool:** Claude Code (Opus 4.6, 1M context)

**PRs:** #141, #142, #143, #144, #145, #148

**Issues closed:** #117, #104, #131, #135, #136, #137, #132, #130,
#133, #140, #139, #138

**Issues created:** #146, #147, #149, #150, #151

**Key changes:**
- New `base/cicd-patterns.md` — 8 reusable CI/CD patterns (gate job,
  path filtering, fan-out, artifact promotion, caching, matrix,
  auto-merge, deploy preview)
- New `base/testing-patterns.md` — 8 test patterns (factory, AAA,
  builder, parameterized, fixtures, mock boundary, snapshot, contract)
- New `frontend/patterns.md` — 8 UI patterns (error boundary, skeleton,
  optimistic update, virtual scroll, debounced search, form validation,
  responsive switch, URL state sync)
- New `base/security.md` — application security rules (12 sections:
  input, output, injection, auth, sessions, secrets, TLS, headers,
  errors, logging, CORS, uploads)
- New `base/security-patterns.md` — 8 app security patterns (slim,
  structural only)
- Rewrote `base/devsecops-patterns.md` — 8 pipeline security patterns
  (break-build gate, triage, SBOM, secret rotation, dep updates,
  security smoke, pre-merge gate, hardening loop)
- Expanded grading scale in `base/360.md` to include +/- modifiers
- Added audit tracking section to `base/360.md`
- Added remediation references section to `base/360.md`
- Batch quick wins: focus-visible, Dependabot, lychee root-dir,
  3 review checks, post-mortems, test factory defaults, sonarjs,
  boolean sort, explicit audit steps, ONBOARDING verify check

**Key decisions:**
- Pattern files are separate from rules files (rules say what,
  patterns say how) — different purposes, different audiences
- Security split: `security.md` (app rules) vs `devsecops.md`
  (pipeline rules), each with its own patterns companion
- Architecture spikes created for composition-over-inheritance
  (#151), pattern resolution (#149), agent-side resolution (#150)

---

## 2026-05-04 — Composition model, folder restructuring, roadmap removal

**Tool:** Claude Code (Opus 4.6, 1M context)

**PRs:** #157, #158, #159, #160, #161

**Issues closed:** #153, #154, #155

**Key changes:**
- Removed `ROADMAP.md` — planned work tracked via GitHub milestones
- Added consumption model section to SPEC.md (declaration block,
  resolution algorithm, lifecycle diagram, two worked examples)
- ADR-005: apply Miller's law (7±2) to repo structure
- Implemented composition model from ADR-004: trimmed quality-gates
  deps, added `core:` tier to manifest, moved 5 pattern files to
  `docs/patterns/`, fixed 3 stale file headers, added explicit
  cicd+devsecops to 13 backend stacks
- Implemented ADR-005 folder restructuring: created `templates/`
  parent (root 12→6 dirs), split `base/` into 5 subfolders
  (core, security, infra, workflow, language), moved SPEC.md to
  `docs/`, moved INTERVIEW.md and manifest.yaml to `templates/`
- Removed `generated/` directory from tracking
- Fixed remote URL (Imbra-Ltd → braboj)
- Enabled auto-merge on repo
- Triaged 6 unlabeled issues with priority labels

**Key decisions:**
- ROADMAP.md replaced by GitHub milestones (no closed milestones
  for completed phases — dev journal covers history)
- Miller's law as organizing principle for folder structure
- SPEC.md belongs in docs/ (documentation, not template source)
- INTERVIEW.md and manifest.yaml belong in templates/ (part of
  the template system)
- Pattern files are human reference docs, not agent context

---

## 2026-05-04 — Release v2.0.0

**Tool:** Claude Code (Opus 4.6, 1M context)

**PRs:** #174, #175, #176

**Issues closed:** #168, #169, #170, #171, #172, #173

**Key changes:**
- First 360-degree audit (`docs/360-audit.md`) — grades: Value B+,
  Quality C+, Viability A-, Discovery D+
- Recovered lost agents.md move from orphaned branch
  `fix/claude-md-review` (formats/ → base/core/)
- Fixed E2E test paths broken after ADR-005 restructuring (27/30
  were failing, CI was red on main for 5+ merges)
- Fixed grpc.md line-1 corruption, README wrong path, PLAYBOOK
  step numbering, stale Imbra-Ltd link, DPL test paths
- Aligned CLAUDE.md with 6-section format spec (added § 4 Identity,
  renamed § 1.1 to Overview)
- E2E tests now gate PRs (moved from push-to-main only)
- Added stale-branch check to session startup and cleanup to
  end-of-session protocol
- Cleaned up 8 stale local/remote branches
- Enabled delete-branch-on-merge, added e2e to required checks

**Key decisions:**
- v2.0.0 due to breaking structural changes: ADR-004 composition
  model, ADR-005 folder restructuring, agents.md relocation,
  6-section format alignment
- Discovery (D+) identified as project bottleneck — needs launch
  post, social card, community presence before v3

---

## 2026-05-04 — v2.1.0 Polish + Quality sprint

**Tool:** Claude Code (Opus 4.6, 1M context)

**PRs merged:** #194, #195, #196, #197, #201, #202, #204, #205,
#207, #209, #212, #214, #216, #223, #225, #226, #227, #228, #229

**Issues closed:** #188, #189, #190, #187, #183, #200, #178, #198,
#199, #206, #208, #211, #213, #215, #217, #218, #219, #220, #221,
#222

**Issues created:** #193–#224

**Releases:** v2.1.0 — Polish

**Key changes:**
- Created 7 milestones (v2.1–v2.5, v3.0, Backlog), assigned all
  29 open issues
- v2.1 Polish: README SEO rewrite, repo description with CLAUDE.md
  keywords, powered-by attribution in INTERVIEW.md, multi-agent
  output clarification, report-an-issue link
- ADR-006: standardized on 3-digit SemVer, added no-build release
  process (GitHub Releases), milestone = minor bump
- Moved release.md from base/infra to base/workflow
- Created base/data/ layer: data-modeling, data-governance,
  data-migration (moved data-quality from base/language)
- Moved config.md from backend to base/core, made stack-agnostic
  (added build-time vs runtime, naming conventions, config
  precedence, 12-factor reference)
- Covered all 12-factor app principles: added dependencies and
  port binding to config.md, disposability and admin processes
  to quality.md
- Covered OWASP Top 10 fully: added deserialization/data integrity
  (A08) and SSRF (A10) to security.md
- Fixed security doc hierarchy: added DEPENDS ON and EXTEND links
  to backend/auth.md, removed duplicated rules
- Template audit (3 parallel agents): found and fixed duplication,
  stale refs, missing DEPENDS ON headers, manifest mismatches
- Moved testability section from quality.md to testing.md
- Refactored backend-quality.md: added EXTEND for security overlap
- Consolidated duplicated testing rules in 4 backend templates
- Stripped all 18 inline "see templates/..." prose references —
  relationships tracked via [DEPENDS ON] headers only
- Added .gitignore guidance to git.md
- Added E2E-01 smoke check (validates cases.py paths resolve)
- Removed dead skipped tests FMT-03/04/05 (27 e2e tests now)
- Disabled wiki on repo

**Key decisions:**
- Inline cross-references are maintenance debt — use [DEPENDS ON]
  headers (machine-validated) instead of scattered prose refs
- Config is a foundational concern (base/core), not backend-specific
- 12-factor and OWASP are methodologies codified across base templates
- Milestones map 1:1 to minor releases (v2.1, v2.2, etc.)
- No-build projects skip chore PR, use tag + GitHub Releases

---

## 2026-05-04 — v2.2 milestone closure

- PR #232: made end-of-session audit steps explicit in CLAUDE.md §6.3
  (closes #139)
- Closed #137 (post-mortem convention) — already in docs.md
- Closed #136 (code review checks) — already in review.md
- Closed #132 (test factory conventions) — already in testing.md
- Moved #224, #203 from v2.2 to v2.5 (better fit for Templates &
  Content)
- Created #233 (spike: naming conventions for issues and PRs) in v2.5
- v2.2 — Quality milestone fully closed

---

## 2026-05-05 — E2E provider infrastructure and product clarity

- PR #235: provider-agnostic e2e runner (closes #100)
  - 5 providers: anthropic, gemini, deepseek, groq, claude-cli
  - Manifest-based dependency resolution (ADR-004 algorithm)
  - Retry with exponential backoff on rate limits
  - Full LLM output + prompt in reports
  - load_dotenv support, .env in .gitignore
- Tagged v2.2.0 (GitHub Release)
- Created #236 (resolve.py script for dependency resolution)
- Created #237 (document all user paths: web, API, agent)
- Created #238 (ADR: generation out of scope, templates are the product)
- Created #239 (expand smoke tests for structure/resolution)
- Created #240 (reduce live e2e to one canary test)
- Created #241 (drop --offline mode)
- Created #242 (audit docs for unsustainable claims)

**Key decisions:**
- Generation is not the product — the template library is
- Local agents (Claude Code, Codex) are the primary user path
- API-based generation has inherent limitations (model fidelity,
  token limits, rate limits) — document, don't guarantee
- Live e2e tests are internal quality tools, not a product feature
- One canary test (python-lib) is more valuable than 27 flaky tests

## 2026-05-06 — v2.3 Tooling batch (P2 sweep)

**Tool:** Claude Code (Opus 4.6, 1M context)

**PRs merged:**
- #245 — ADR-007: generation is out of scope (docs/decisions/)
- #250 — Agent secrets handling rules (security-agent-secrets)
- #246 — Expanded smoke tests: MNF-02, MNF-03, MNF-04 (8 → 11 checks)
- #247 — E2e canary default (STK-15 python-lib, --all flag)
- #248 — Drop --offline mode, delete e2e.yml workflow
- #249 — tools/resolve.py + 30 pre-resolved files in generated/

**Issues closed:** #238, #239, #240, #241, #236, #244

**Key changes:**
- Smoke suite now validates manifest resolution for all stacks
- Default `py tests/run_e2e.py` runs only the canary test
- `tools/resolve.py` implements ADR-004 resolution (--list, --concat,
  --generate, --check)
- `generated/` directory committed with pre-resolved chain per stack
- `sync.py --check` now validates generated/ files
- Branch protection updated: only `smoke` required (removed `e2e`)
- run_e2e.py refactored to use shared resolver from tools/resolve.py

## 2026-05-31 — Viability spikes and milestone-rule fix

**Tool:** Claude Code (Opus 4.7, 1M context)

**PRs opened:**
- #353 — Require milestone on every GitHub issue (closes #352)

**Issues created:**
- #349 — Spike: deep-knowledge + tutorial-extraction workflow
  (v3.0 — Restructure, P3)
- #350 — Spike: viability audit — does solid-ai-templates deliver
  repeatable SOLID-grade quality? (v3.0 — Restructure, P2)
- #352 — Enforce milestone-on-every-issue convention in
  platform/github.md (v2.5 — Conventions, P2)

**Issue grooming:**
- Triaged 13 open issues: every open issue now has type + priority
  + milestone (#332, #333, #334, #335, #337, #344, #345, #348,
  #351, #354, #355, #356, #357)
- New convention-rule issues parked in v2.5; restructure-scope
  issues in v3.0

**Key changes:**
- Milestone rule added to `templates/platform/github.md` under
  the existing `[EXTEND: base-issues-types]` block — milestones
  are a GitHub feature, so the rule belongs in the platform layer,
  not in platform-agnostic `base/workflow/issues.md`
- Two spikes opened motivated by me-fuji CLAUDE.md bloat (29KB,
  349 lines) and its forced 17-file SessionStart preload: #349
  proposes a three-layer knowledge model (conventions / deep
  knowledge / extractable tutorials), #350 is the broader
  viability meta-audit

**Process notes:**
- First pass at the milestone rule landed in the wrong layer
  (base instead of platform) and was duplicated in this repo's
  own CLAUDE.md — caught during template re-read, reverted, and
  reapplied correctly. Root cause: skipped the §6.1 startup
  template read before editing the templates themselves.
- Reinforces the case for #330 / #355 (mandatory template-file
  reads at session start) — even with the rules visible, an
  agent that doesn't read them edits at the wrong layer.

**Lessons captured:** these are template-relevant, not
project-specific — the layer-placement discipline (platform-
specific concepts belong in the platform template, not base)
should be reflected in #354's doc-placement decision tree when
that issue is worked.

**Continued — v2.5 closeout:**

After the spike work, picked up v2.5 — Conventions one by one.
All 12 originally-open v2.5 issues plus #352 (filed and merged
during session) are now closed. Milestone shows 14 closed / 0 open.

**PRs merged (continued):**
- #353 — Require milestone on every GitHub issue (#352)
- #359 — Forbid force-push, even --force-with-lease (#329)
- #361 — De-stack a PR by branching fresh + cherry-pick (#336)
- #362 — Add GitHub Release step to with-manifest release path (#338)
- #363 — Add doc-placement decision tree (#354)
- #365 — Rewrite end-of-session step 6 around content rules (#355)
- #366 — Agent context trade-offs pattern doc (#356)
- #367 — Multi-template loading + template dilution coverage (#356)
- #370 — Split template content quality into docs/meta/ (#356)
- #371 — Agent output style rule (#351)
- #372 — Match document convention rule (#357)
- #373 — Branch cleanup at session startup (#326)
- #374 — YAGNI revisit trigger discipline (#340)
- #375 — Import-time env mutation testing rule (#341)
- #376 — CodeQL paths-ignore for captured fixtures (#343)
- #377 — Skip noisy gates on equivalent-input PRs (#348)

**Issues created (continued):**
- #364 — Smoke check SYS-02 false-positive on inline ID refs
  (bug, Backlog)
- #368 — Spike: measure cold-start and template-loading cost
  (scopes 1+2, v3.0)
- #369 — Spike: cross-window cold-start comparison (Backlog,
  blocked on #368)

**Key changes:**
- New docs/meta/ folder for library-facing reference material
  (agent-context-tradeoffs.md, template-content-quality.md) —
  distinct from docs/patterns/ which is project-facing
- Agent-behavior cluster in base/workflow/ai-workflow.md now
  covers four rules: doc placement, end-of-session content,
  output style, document-convention matching
- base/core/git.md gains three rules: no-force-push, de-stack PR,
  optional gh release create step
- base/core/quality.md YAGNI bullet extended with revisit-trigger
  discipline
- base/core/testing.md gains env-mutation-isolation rule
- platform/github.md gains milestone requirement and CodeQL
  paths-ignore for fixtures
- base/workflow/quality-gates.md gains conditional-skip pattern
  for noisy output gates
- base/workflow/scope.md session startup gains branch cleanup
  step (step 5), end-of-session step 6 rewritten around
  doc-placement decision tree

**Process notes (continued):**
- Switched mid-session to `gh pr merge --auto --squash
  --delete-branch` per user direction — saved time on the long
  v2.5 sweep
- The PR #370 saga (mid-PR split into two files, then folder move
  to docs/meta/) illustrated the doc-placement decision tree
  *operating in real time*: the dilution discussion outgrew its
  host file, then the new file revealed it didn't belong in
  patterns/. Both reorganizations were the right call mid-stream.

**Lessons captured (continued):** the v2.5 closeout demonstrates
that small, focused, well-anchored PRs scale well with auto-merge.
The agent-behavior cluster in ai-workflow.md ended up as four
sibling sections — proves the YAGNI hold from #354 (don't pre-emptively
create agent-behavior.md) was correct. The split into docs/meta/
was the right move when content actually accumulated.
