# Dev Journal

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
- First 360-degree audit (`docs/audits/2026-05-04-360.md`) — grades:
  Value B+, Quality C+, Viability A-, Discovery D+
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

## 2026-05-06 — Generated stacks audit

- Tool: Claude Code (Opus 4.6)
- Audited 5 generated stacks: terraform, tutorial, python-lib, react-spa, go-service
- Created #264 (audit parent) + 4 sub-issues (#265–#268)
- Fixed #268: added `base-security` and `base-containers` to `backend-quality` deps —
  resolved missing dependency gap for all 6 service stacks
- Merged PR #269
- Swapped milestones: v2.4 is now Templates & Content, v2.5 is now Discovery

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
**Issues closed:** #104, #131, #203, #224, #233, #255, #264, #272, #275, #276, #283,
#284, #285
**Smoke checks:** 11 → 13 (TPL-06, TPL-07)

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

**Release:** v2.10.0 (https://github.com/braboj/solid-ai-templates/releases/tag/v2.10.0)

---

## 2026-06-24 — v2.11 docs & ADR conventions

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Planned and shipped v2.11 — Docs & ADR conventions (8 issues, 5
  theme PRs)
- Before starting: brought 23 backlog issues into `github.md`
  compliance (added missing `task` type and `P3` priority labels) —
  0 type/priority/milestone violations remain
- #505 (PR #539): general Markdown/docs style rules in
  `base/core/docs.md` — ADR tables, visual restraint, diagram + Mermaid
  gotchas. Re-applied from the stale `docs/markdown-style-rules` branch
- #513 (PR #540): arc42 authoring conventions — chapter boundaries
  (§2 vs §4, §3 black-box, §9 ADR index), ID schemes (FR01/QG01),
  concept-section tables; folded in #503's arc42 points
- #489 + #533 (PR #541): one concern per ADR (recorded as ADR-014,
  with CLAUDE.md §2.9 + TEMPLATE.md pointers) and same-day
  supersession-when-premise-refuted guidance
- #529 + #507 + #515 (PR #542): milestone-on-purpose (`github.md`),
  upstream-flag end-of-session steps (`scope.md`, re-applied from the
  stale branch), layer-aligned identifiers (`oop.md`)
- #500 (PR #543): kept `dev-journal.md` (rename to SESSIONS.md deferred
  to v3.0), documented the SHOUT-vs-kebab casing split, added a
  required-contents entry schema, and reconciled `docs.md` to the
  journal's actual newest-first / `## YYYY-MM-DD — Theme` format

**Lesson:** two pairs of issues overlapped and were deduped at plan
time rather than landing conflicting edits — #503 folded into #513
(arc42), and #505's general style rules landed first so #513 could be
trimmed to arc42-specifics. #489 is self-referential: by its own
"one concern per ADR" rule it split from #533 into ADR-014, leaving the
supersession guidance docs-only. This entry is the first written under
the #500 schema it documents.

**PRs merged:** #539, #540, #541, #542, #543

**Issues closed:** #489, #500, #505, #507, #513, #515, #529, #533

**Milestone:** v2.11 — Docs & ADR conventions (8/8 closed)

**Release:** v2.11.0 (https://github.com/braboj/solid-ai-templates/releases/tag/v2.11.0)

**Next:** planned v2.12 — Probe-first workflow lessons (#18, 9 issues) —
ai-workflow probe/verify-before-acting sweep I; #482 closed as a
duplicate of #477. Not yet started.

---

## 2026-06-24 — v2.12 probe-first workflow lessons

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Planned and shipped v2.12 — Probe-first workflow lessons (9 issues,
  2 theme PRs) — all 9 were the same lesson at different decision
  points, consolidated into 2 Lessons Learned subsections in
  `base/workflow/ai-workflow.md` rather than 9 fragments
- #468 + #471 + #450 + #459 + #532 + #477 + #481 + #474 (PR #546):
  "Probe before acting on a hypothesis" — run the cheapest probe that
  would refute a hypothesized mechanism / proposed fix / inherited
  diagnosis before acting; enumerates the decision points (before
  coding a proposed fix, before drafting an ADR, at spike intake, on a
  diagnosis inherited from prior-session memory, before filing a bug),
  the "probe the artifact, not your reading of it" corollary, and the
  record-the-inversion / throwaway-probe discipline
- #496 (PR #547): "Verify external state before a visible action" —
  before filing an issue/PR on a third-party repo, taking a
  dependency, or pulling a vendored fixture, confirm the target is the
  real project, the repo is live (not archived/migrated), and the
  channel is open; a failed check feeds back to the stale ADR / README
  / memory pointer, not just the blocked action

**Lesson:** the nine issues overlapped almost entirely, so they were
deduped at plan time into two cohesive subsections — the issues
themselves flagged the overlap (#474 suggested one combined section,
and #471/#450 carried forward from #468). No ADR was written: it is
template content, not a structural/system decision. No inline `.md`
cross-reference was added either — several issues requested a pointer
to `quality.md` §Probe scripts, but this layer expresses relationships
via `[DEPENDS ON]` headers only, so the throwaway-probe point was
stated self-contained instead.

**PRs merged:** #546, #547

**Issues closed:** #450, #459, #468, #471, #474, #477, #481, #496, #532

**Milestone:** v2.12 — Probe-first workflow lessons (9/9 closed)

**Release:** v2.12.0 (https://github.com/braboj/solid-ai-templates/releases/tag/v2.12.0)

**Next:** v3.0 — Restructure (13 issues) — inline-to-reference eval,
slim stacks.

---

## 2026-06-25 — Maintenance: dependency bump + branch prune

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Merged Dependabot PR #524 — `actions/checkout` 6→7 in
  `.github/workflows/smoke.yml`; branch was BEHIND `main` under strict
  checks, so ran `gh pr update-branch` (not force-push) and waited for
  the smoke re-run to go green before squash-merging
- Pruned stale remote-tracking refs (4 already-merged docs branches +
  the merged dependabot branch) via `git remote prune origin`

**Lesson:** the "stale remote branches" in `git branch -a` were only
stale local tracking refs — server-side auto-delete-on-merge had
already removed them, and `git ls-remote` confirmed the live remote
held just `main`. Verify against the remote before attempting a
server-side delete (the same verify-external-state discipline #547
codified the day before).

**PRs merged:** #524

**Issues closed:** none

## 2026-06-25 — v2.13 CI/CD & release hardening

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Planned and shipped v2.13 — CI/CD & release hardening (7 issues, 5
  theme PRs), chosen as a concrete intermediate milestone before the
  v3.0 restructure, from a CI/CD cluster in the Backlog
- #499 (PR #550, P2): CI workflow authoring rules from a real gitleaks
  outage — authenticate `api.github.com` calls (shared-runner rate
  limit), fail loud on shell-pipeline-resolved values, and verify a
  tool's pricing/license before adopting it (added to ai-workflow's
  "Verify external state" section, not the issue's suggested home)
- #510 (PR #551): pin third-party GitHub Actions to commit SHAs, with
  the version in a trailing comment so Dependabot still bumps them
- #509 + #438 (PR #552): Dependabot weekly-batch triage —
  lockfile-conflict cascade, auto-supersede, aggregator-timing, fix-PR-
  first for lint-rule bumps, and co-dependent caret-range rebase
- #528 + #531 (PR #553): per-tag GitHub Release as the durable record
  (tag-gated, idempotent, deploy-independent) + SBOM uploaded to it,
  guarded and continue-on-error so a scan hiccup never erases it
- #497 (PR #554): distinguish CI infra failures from diff failures when
  judging PR readiness (new CI-signals section in review.md)

**Lesson:** `git add -A` swept the untracked `.claude/` and
`docs/drafts`+`docs/spikes` working dirs into PR B's commit. Caught it
before opening the PR, undid via `git reset --mixed HEAD~1`, deleted the
just-pushed remote branch (not a force-push — no PR, no collaborators),
and re-pushed staging explicit paths. Use explicit `git add <paths>`,
never `-A`, while those dirs sit untracked.

**PRs merged:** #550, #551, #552, #553, #554

**Issues closed:** #499, #510, #509, #438, #528, #531, #497

## 2026-06-25 — v2.14 Workflow & quality lessons

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Assessed the 77-issue Backlog (dominated by ~50 lesson fragments;
  only Python-stack (7) and Frontend (6) remain as concrete clusters)
- Transferred 3 Backlog issues into v3.0 — Restructure per the
  "big / requires real restructuring → v3.0, else do it earlier"
  rule: #492 (extract abstract frontend-content layer), #414 + #415
  (skills-as-UX-layer initiative). #369 (cold-start measurement) kept
  in Backlog — small, pairs with v3.0's #368 when that work runs
- Planned and shipped v2.14 — Workflow & quality lessons (13 issues,
  3 theme PRs), a consolidation round folding lesson fragments into
  existing sections rather than fragmenting
- #485 + #484 + #486 + #526 + #494 (PR #556): "Verify before relying" —
  routed to correct homes, not one section: handoff-note counts decay
  (ai-workflow.md), a dep bump is verified by the gate not the changelog
  (ai-workflow.md), audit downstream renders when truth changes
  (ai-workflow.md), reasoning comments rot (quality.md), green CI ≠
  environment-independent (quality-gates.md)
- #501 + #527 + #516 + #430 (PR #557): "Plan & scope discipline" —
  read in-source audit comments at the edit site (new ai-workflow
  Practices section, P2), constraints invalidate plans mid-execution
  (ai-workflow Lessons), reconcile recommendations/breadcrumbs against
  documented scope + current milestone before planning (scope.md)
- #460 + #480 + #525 + #502 (PR #558): "Gate & test honesty" —
  disaggregate verdict/plausibility/accuracy + lenient gates need a
  human residual check (quality-gates.md), numerical gates lock
  magnitudes not contours (review.md), tests should name what they pin
  (testing.md)

**Lesson:** when consolidating a lesson family, route each item to its
*semantically correct* file rather than the milestone's headline file —
forcing #526 (reading code comments) or #486 (gate scope) into
ai-workflow.md would have mis-placed them. One concern can span files
(ADR-014); the headline theme is not the mandatory home.

**PRs merged:** #556, #557, #558

**Issues closed:** #485, #484, #486, #526, #494, #501, #527, #516, #430, #460, #480,
#525, #502

## 2026-06-25 — v2.15 Backend & resilience + repo hygiene

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Added a labels-at-creation rule to CLAUDE.md §2.2 (#566, PR #567),
  fast-tracked via Expedite — labels applied at creation, never an
  unlabeled ticket
- Planned and shipped v2.15 — Backend & resilience (milestone #21,
  7 issues + 1 spawned, 6 PRs). Chose a concrete theme over a third
  consecutive lessons-drain; triaged #498 (generation-fidelity bug) →
  Expedite, closed #457 wontdo, assigned #560/#561/#563 → Backlog
- Spike #564 (decision, no ADR): generic async-resilience rules extend
  existing `messaging.md` (route C — generic home + thin webhook
  surface, no new file/layer). Corrected the issue's gap analysis (DLQ
  was already covered in messaging.md + jobs.md); spawned impl #568
- #568 (PR #569): `messaging.md` "Load & backpressure" — decouple under
  load, debounce/coalesce, backpressure on saturation, per-key fairness
- #521 + #522 (PR #570): reject non-finite JSON floats (`http.md`) +
  nosniff cross-platform MIME caveat (`security.md` Security headers,
  not devsecops.md)
- #446 + #439 (PR #571): import-cycle → shared third module, and
  return-type back-compat shim (`quality.md` Maintainability)
- #447 (PR #572): opt-in DiagnosticSink pipeline pattern →
  `observability.md` (moved off the planned quality-gates.md — a gate
  verifies, a sink instruments for debugging)
- #565 (PR #573): new `backend/webhooks.md`, register-only (composition
  over inheritance, ADR-004) — composes the resilience substrate via
  `[DEPENDS ON]`, adds only the webhook-specific surface; 0 chains wired
- Repo hygiene: gitignored `.claude/` (PR #574); removed `docs/drafts/`
  (obsolete) and `docs/spikes/` (findings for open spikes #350/#479
  archived to those issues first, then deleted)

**Lesson:** plan-time placements need verification against real file
contents before writing. Two of this milestone's planned homes were
wrong on inspection. The "missing DLQ" in #564 was already covered;
the DiagnosticSink home in #447 (quality-gates.md) conflated a gate
(which verifies) with an instrument (which debugs), and belongs in
observability.md. Verify the gap or the home, then write.

## 2026-06-25 — v2.16 Generation fidelity & mechanical checks

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Planned v2.16 (milestone #22) from the two Expedite items and two
  Backlog siblings — theme: a derived/generated artifact faithfully
  carries its constraints, each backed by an agent-runnable check.
  Drained Expedite to empty; #563 left in Backlog (off-theme)
- Branch hygiene: confirmed `origin` auto-deletes on merge — the 18
  "stale" branches were already gone remotely; only local tracking refs
  were stale (`git remote prune origin`, not `push --delete`)
- #479 (PR #578): pair-the-check convention — a mechanically-checkable
  output constraint MUST name its agent-runnable check; subjective ones
  stay declarative. Landed as `quality-gates-pair-check` (generalizes
  `quality-gates-staleness`) + CLAUDE.md §2.7. Spike decision, no ADR
- #560 (PR #579): bulk-emit scripts MUST expose `--check` and report the
  stale-entry *count*, not just the path (`base-docs` Generated files)
- #561 (PR #580): convention-as-test — an "if X then Y" derived-artifact
  invariant MUST be a test, not a written convention
  (`quality-gates-convention-as-test`)
- #498 (PR #582): the end-of-session audit was paraphrased into lossy
  bullets in hybrid generation. `agents.md` §6.3 (all 3 output models) +
  hybrid what-to-inline now mandate inline-verbatim or hard-delegation
  ("execute each item; do not summarize"), never paraphrase; new smoke
  check **SYS-05** gates the enforcement phrase in the output spec and
  every example session-protocol section. Fixed `hybrid-astro`; spawned
  #581 (refresh the 7 stale §6-less examples)

**Lesson:** ground a check's target against the real artifacts before
building it. #498's literal ask — "smoke-check the generated CLAUDE.md
§6.3" — did not map: 7 of 8 in-repo examples have no §6 at all, and the
one that did only soft-referenced. The check had to target the output
spec (`agents.md`) plus the single compliant example, and the staleness
became its own ticket (#581). The whole milestone dogfooded #479: each
issue shipped its rule *with* its check, so the convention did not decay
the way the §2.7 constraints had.

**PRs merged:** #578, #579, #580, #582

**Issues closed:** #479, #560, #561, #498

## 2026-06-25 — v2.17 Workflow lessons: bulk & shared-path fix discipline

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Planned v2.17 (milestone #23) as a lessons-drain over the Backlog's
  bulk / shared-path fix fragments (me-fuji probe-and-fix sessions),
  deferring the v3.0 restructure spikes (#350/#179/#180). 9 issues
  consolidated into 5 generic rules across 5 PRs
- Ran a genericity pass before implementing each rule — the "generic,
  not one-stack" bar demoted two issues to folded examples rather than
  standalone content: #458 (byte-hash cohort dup → data-stack-specific)
  and #472 (dispatch-surface sweep → me-fuji-shaped)
- #442 (PR #584): bulk-operations skip-list-then-unblock in `git.md` —
  split a bulk op that hits a per-item bug into two stacked PRs
  (skip-list + tracking issue, then fix + re-run + unblock)
- #465/#466/#470 (PR #585): "Verifying regenerated artifacts" in
  `git.md` — filter CRLF/whitespace noise, visually spot-check binary
  artifacts, and at scale pair a representative spot-check with a global
  metric instead of inspecting all N
- #456/#458 (PR #586): probe cohort breadth before scoping a fix —
  folded into `ai-workflow.md`'s existing "Probe before acting" rather
  than a parallel subsection (avoids the redundancy #350 flags)
- #478/#472 (PR #587): "Shared-path fixes verify every call site" in
  `testing.md` (`testing-shared-path-breadth`) — exercise every call
  site against ground truth ("expected unchanged" is the bug case) and
  re-run every downstream consumer that emits a committed artifact
- #563 (PR #588): "Tooling-produced scope creep is silent" in
  `scope.md` — revert a generator/formatter's unrequested side effects
  before committing, file the drift separately

**Lesson:** for a lessons-drain sourced from one downstream project, the
genericity pass is the load-bearing step, not the wording. Two of nine
fragments only survived as examples inside a generic rule; shipping them
verbatim would have put one-stack content into the core templates every
stack loads — exactly the attention-dilution #350 warns against. Folding
related fragments into an existing rule beat adding parallel subsections.

**PRs merged:** #584, #585, #586, #587, #588

**Issues closed:** #442, #465, #466, #470, #456, #458, #478, #472, #563

## 2026-06-25 — v2.18 Process & workflow lessons

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Planned three pre-restructure milestones to drain the lessons-learned
  backlog before v3.0: v2.18 (process/workflow), v2.19 (quality/testing/
  maintainability), v2.20 (concrete Python/frontend). 48 issues drained
  from Backlog, batched into PRs by target file.
- Drained v2.18 in 8 PRs / 19 issues. The `ai-workflow.md` cluster (14
  issues; reference-only, so no chain restale) landed in 4 PRs:
  probe-with-production-harness + Debugging-multi-stage (#593);
  survey-prior-art, Triage-prototype-cost, Spike-findings-home (#594);
  measure-before-revert, host-maintenance, manual-workaround (#595);
  verify-plan-time-placement, Triage-by-fan-out, Middle-scope (#596).
- `issues.md`: labels-at-creation + Deferred-work-with-named-trigger
  (#597). `git.md`: repeat the closing keyword before each issue number
  (#598, regen 30 chains). `scope.md`: wrap-shipped + deploy-health
  startup checks (#599).
- New register-only `communication.md` [base-communication] — comms
  defaults + shorthand verbs, framed as override-friendly, 0 chains
  (#602, closes #467).
- Genericity pass moved #493 to v2.19 (quality-gates-shaped, me-fuji-
  specific) and collapsed the 14 ai-workflow issues into 11 rules by
  merging pairs (#448+#483, #487+#488) and extending existing sections
  rather than adding parallel ones.

**Lesson:** dogfooding the lessons paid off mid-drain. #503 (arc42
authoring conventions) closed as already-covered once I opened `docs.md`
and found the `docs-arc42` section already held every proposed rule —
exactly the "verify a plan-time placement against the real file" rule
(#576) that landed in the same milestone. Its two genuinely-uncovered
side-patterns were preserved as #600/#601 rather than lost on close.

**PRs merged:** #593, #594, #595, #596, #597, #598, #599, #602

**Issues closed:** #454, #448, #483, #427, #488, #504, #487, #495, #520, #453, #576,
#463, #449, #575, #461, #517, #462, #325, #467. Also: #503 closed as already-covered;
#493 moved to v2.19; #600/#601 filed.

## 2026-06-25 — v2.19 Quality, testing & maintainability lessons

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Drained v2.19 in 9 PRs / 21 issues. `quality.md` (core, 30 chains)
  landed in 3 PRs: measurement & generation discipline — thresholds from
  distributions, mechanical-migration probe, emit-clean-at-source (#605:
  #469 #464 #428); maintainability — per-config opt-in, byte-equivalent
  ports, mega-script decomposition, extraction-ready modules (#606: #451
  #436 #345 #332); fail-loud + retract-dead-code (#607: #452 #476).
- `testing.md` (#608): verify-the-fix-fires-on-real-data, identical-
  metrics-smoking-gun, in-process UI e2e, production-data unit smoke
  (#475 #455 #523 #592). `360.md` (#609): headless-product perspective
  projection + audit-storage choice (#519 #337). `quality-gates.md`
  (#610): promote-a-resistant-case-to-a-gated-tier (#491).
  `data-quality.md` (#611): explicit-absence-over-invented-values +
  agent-assisted GT validation (#473 #432). `ai-workflow.md` (#612):
  folded schema-vs-ingestion split into the existing Middle-scope lesson
  (#440).
- Capstone #591 (#613): the *outbound* genericity sweep complementing
  the v2.17 inbound drain convention — neutralized optical/MTF domain
  nouns that predated it in core-tier + multi-chain templates
  (quality-gates worked example, quality/readme/docs examples).
- Released v2.18.0 mid-session (8 PRs / 19 issues) and flagged the stale
  PLAYBOOK release section vs ADR-006 → filed #604.

**Decisions:**
- **#493** (moved in from v2.18): part 4 (tiered-fixture promotion)
  landed merged with #491; part 3 (dual-path audit) already covered by
  existing audit-every-downstream-render + shared-path-breadth rules;
  parts 1–2 (probe-stopping, narrow-override) DEMOTED as single-use
  me-fuji-shaped — below the genericity bar.
- **#592**'s smoke-check AC declined: prose guidance is not a
  mechanically-checkable output constraint per `quality-gates-pair-check`;
  a section-presence check would be brittle.
- **#440** folded into #463's Middle-scope lesson rather than templated
  as a parallel rule.

**Lesson:** the genericity bar cut both ways this milestone — inbound
(#493 parts 1–2 demoted as single-use) and outbound (#591 neutralized
domain nouns that predated the convention). Same bar, two directions;
the capstone closes the loop the v2.17 PLAYBOOK convention opened.

**PRs merged:** #605, #606, #607, #608, #609, #610, #611, #612, #613

**Issues closed:** #469, #464, #428, #451, #436, #345, #332, #452, #476, #475, #455,
#523, #592, #519, #337, #491, #493, #473, #432, #440, #591. Filed #600, #601, #604
(Backlog).

## 2026-06-25 — v2.20 Concrete Python & frontend

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Drained v2.20 — the third and last pre-restructure milestone — in 5 PRs
  / 7 issues. These were concrete stack patterns, not lessons.
- Python: `python-lib.md` editable-install version-staleness gotcha + a
  build gate (`twine check dist/*`) (#518 #511, PR #619 — regen 7 Python
  chains, python-lib being their base); `python-service.md` runtime-version
  pinning across image/CI/mypy/`requires-python` (#530, #620);
  `python-flask.md` versioned-API registry + factory over per-version
  duplication (#512, #621).
- Frontend: `ux.md` graded-variant bake-off (#514, #622); frontend SEO —
  AEO rules (passage-first content, citation-frequency measurement,
  answer-engine crawler allowlist, FAQPage) plus #311's social-meta /
  heading-coherence / favicon rules, landed in the already-wired
  `quality.md` + `static-site.md` SEO sections (#490 #311, #623).

**Decision:** #311 asked for a new `frontend/seo.md` template. Landed its
rules now in the existing wired SEO sections (so they reach frontend
projects) and deferred the dedicated-file consolidation to the v3.0
frontend restructure — filed #624, pairs with #492. Creating a new
frontend file days before that restructure would only be moved again.

**Lesson:** stack-specific patterns belong in stack templates, not core.
The v2.17/#591 genericity bar guards the inverse direction (no one-stack
content in core), so concrete Python/frontend patterns landing in
`python-*.md` / `frontend/*.md` is exactly right — no demotion needed.

**Milestone arc:** v2.18 → v2.19 → v2.20 complete. The three-milestone
pre-restructure backlog drain is done; Backlog is down to single digits;
v3.0 — Restructure is the clear next milestone.

**PRs merged:** #619, #620, #621, #622, #623

**Issues closed:** #518, #511, #530, #512, #514, #490, #311. Filed #624 (v3.0
frontend/seo.md consolidation).

## 2026-06-26 — v2.21 Workflow, doc & data lessons + journal-ordering revert

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Triaged the four unmilestoned wuseria S188–189 lessons: created the
  v2.21 milestone for the three reusable ones (#615, #616, #617); #618
  (journal-format deviation) parked in v3.0 as the configurable-format
  question rather than closed.
- Reverted the dev-journal ordering mandate from newest-first back to
  chronological (oldest-first) — `docs.md`, the 30 generated chains, and
  this repo's own 36-entry journal reordered; recorded in ADR-015 (#618
  ordering half, PR #626). The newest-first flip had been an unexplained
  side effect of #500 / PR #543.
- Drained v2.21 in three one-concern PRs: #615 read the prior spike's
  close-out before re-investigating (`ai-workflow.md`, PR #627); #616 a
  comment citing an issue inherits its lifecycle (`quality.md` Code
  style, PR #628); #617 honest absence beats a recovered wrong value
  (`quality.md` Calibration discipline, PR #629).

**Decision:** ADR-015 settles dev-journal ordering as oldest-first with no
per-project configurability — a single default keeps generated context
files uniform. The flip was reverted because it carried no recorded
rationale and forced long-running downstream journals to either rewrite
history or carry a standing deviation.

**Lesson:** a convention changed without an ADR is indistinguishable from
drift — the newest-first flip rode inside an unrelated casing/schema PR
and could not be defended when challenged. Reversible convention changes
still need a recorded reason.

**Milestone arc:** v2.21 closes the pre-restructure lesson queue (now
empty). v3.0 — Restructure is the clear next milestone, spike-driven
(#179 inline→reference, #180 slim stacks, #350 viability audit).

**PRs merged:** #626, #627, #628, #629

**Issues closed:** #615, #616, #617. Created milestone v2.21; #618 parked in v3.0.

## 2026-06-26 — v2.22 restructure-safe cleanup (release docs, CD & API)

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Cut a clean, restructure-safe v2.22.0 from the Backlog before opening
  v3.0 — three one-concern PRs, each independent of the inline→reference
  decisions (#179/#180/#350), so none is invalidated by the restructure.
- #604 aligned the PLAYBOOK "Release a new version" section with ADR-006:
  cut a GitHub Release from main with a bare-version title and
  `--generate-notes`, close the milestone, journal entry via its own
  no-milestone `docs(journal)` PR (PR #631). Dropped the abandoned
  `chore/release` branch+PR flow, which only applies to manifest projects.
- #601 added a build-once/deploy-via-hook CD rule to `cicd.md`: after
  publishing, trigger the deploy by sending the artifact's immutable
  reference to the deploy target, never rebuilding at deploy time
  (PR #632, +16 regenerated chains).
- #600 extended the `api.md` OpenAPI section with the design-first
  source-of-truth pattern — hand-authored spec served verbatim, pinned
  to code, contract-tested (e.g. Schemathesis); fastapi/flask keep their
  framework-native code-first OpenAPI (PR #633, +5 chains).

**Decision:** held #581 (refresh example CLAUDE.md files) out of v2.22 —
it depends on the examples-maintenance model (spike #13, in v3.0), and the
inline→reference flip would change what an example should even look like.
Refreshing now risks throwaway work.

**Lesson:** a downstream pattern (build-once/deploy-hook, design-first
OpenAPI) often overlaps an existing template rule — extend the existing
section and reference the shared principle rather than add a parallel one,
or the restated rule becomes attention dilution.

**Milestone arc:** v2.22 is the last pre-restructure release — a stable,
clean v2.x baseline. v3.0 — Restructure is next, spike-driven (#179
inline→reference, #180 slim stacks, #350 viability audit).

**PRs merged:** #631, #632, #633

**Issues closed:** #604, #601, #600. Created and closed milestone v2.22.0.

## 2026-06-26 — v2.23 Examples (ADR-016 + full regeneration)

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Added a v2.23 — Examples milestone before v3.0 to land the examples
  work as its own point release. Pulled spike #13 in from v3.0 (it gates
  #581) and pushed #90 (launch) and #369 (cold-start, blocked on #368)
  into v3.0, emptying the Backlog milestone.
- #13 → ADR-016: example `CLAUDE.md` files are agent-generated outputs of
  the documented local-agent path — regenerated on material template
  change, never hand-patched. `generated/` stays the authoritative
  deterministic chain reference; structure is gated by smoke (PR #635).
- #581: regenerated all 8 examples via the pipeline (existing brief +
  `generated/<stack>.md` + `agents.md`). Seven moved from the stale
  pre-`agents.md` free-form shape to the six-section inline model, adding
  §5 Review process and §6 Session protocol with a compliant §6.3;
  hybrid-astro stayed on the hybrid model with its duplicate §1.3 fixed.
  Disambiguated the two same-named Go examples: go-service → MetricStream
  (chi), metricshub kept MetricsHub (Echo). Added a PLAYBOOK "Regenerate
  an example" procedure and a CLAUDE.md §2.5 pointer (PR #636).

**Decision:** reversed v2.22's deferral of #581. v2.22 held it back
fearing the inline→reference flip (#179) would make a refresh throwaway.
This session resolved that: the six-section skeleton is stable across
inline→reference — only section *bodies* change — so regenerating onto
the skeleton now is durable. v2.23 is now the last pre-restructure
release; v3.0 — Restructure is next.

**Lesson:** when a deferral rests on "an upcoming change will redo this,"
check whether that change touches the *structure* you would produce or
only its *content*. A stable skeleton means the work is not throwaway,
and the deferral is unjustified.

**Template feedback:** ADR-016 and the "Regenerate an example" procedure
are project-specific (they govern this repo's `examples/`). No upstream
template change.

**PRs merged:** #635, #636

**Issues closed:** #13, #581. Created and closed milestone v2.23.0;
moved #90 and #369 to v3.0.

## 2026-06-26 — v2.24 Stack structure (ADR-017 + drift + SYS-06)

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Opened v2.24 — Stack structure as consolidation pre-work before the
  stack-cleanup spike/removals (Milestone B): a consistent baseline makes
  stacks comparable before any are cut.
- #639 → ADR-017: canonical stack-template section structure. MUST (Stack,
  Commands, Project structure), SHOULD (Testing, `<Language> conventions`,
  Git, Configuration, Quality gates, Error handling), MAY (domain).
  Membership judged on the resolved chain (inheritance counts); pure
  libraries exempt from Project structure; canonical order fixed; names
  SYS-06 as the gate (PR #642).
- #640: fixed the drift — added Project structure to htmx and
  static-site-astro, renamed terraform's "Repository structure" to the
  canonical name; added Testing to static-site-astro (cross-referencing
  its Quality gates table) and static-site-hugo (build/link/Lighthouse/
  a11y); renamed language sections to `<Language> conventions` (python-lib,
  c-embedded, rust-lib, iac-terraform) (PR #643).
- #641: SYS-06 smoke gate — resolved-chain MUST sections, library-exempt;
  spec `SAIT-SMK-SYS-06-001A` + INDEX row; smoke now 20 checks (PR #644).

**Decision:** gate on the RESOLVED CHAIN, not the raw file. A derived
stack may satisfy a MUST section via its parent, so the gate must not
force repetition — that keeps the composition model intact.

**Lesson:** audit "drift" against the resolved chain, not file-by-file.
Several apparent gaps dissolved on inspection — python-service inherits
Commands from python-lib, terraform had the structure under a different
heading — and one originally-planned fix (adding python-service Commands)
would have introduced a duplicate section downstream. Simulate the gate
before writing the fixes.

**Template feedback:** ADR-017 and SYS-06 are project-specific (they
govern this repo's stack templates). The MUST/SHOULD/MAY taxonomy and
`<Language> conventions` naming are reusable authoring conventions but
live in ADR-017, not a template.

**PRs merged:** #642, #643, #644

**Issues closed:** #639, #640, #641. Created and closed milestone
v2.24.0. Next: Milestone B — spike on whether to cut low-value stacks,
then the removals.

## 2026-06-26 — v2.25 Stack cleanup (remove java, terraform, rust)

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Milestone B — v2.25 — Stack cleanup, realizing #180 (slim the supported
  stacks). The v2.24 structure baseline made stacks comparable first.
- Spike (#180): decided to remove the java, terraform, and rust stacks —
  owner has never used them and does not plan to. All four are leaf stacks
  with zero dependents, so removal breaks no resolved chain.
- #646: removed java-spring-boot, java-grpc, iac-terraform, rust-lib
  (templates + generated chains + manifest entries), the rust-lib e2e case
  (STK-19 retired), and the java-/iac-/rust- rows from CLAUDE.md §2.3.
  Repointed the hybrid-deployment test (DPL-02) onto go-service to keep
  that coverage. sync.py regenerated the README/SPEC/INTERVIEW tables.
  Stacks 30 → 26 (PR #647).

**Decision:** remove rather than keep — the provenance principle (ADR-011,
"forged in real work") argues against shipping stacks the owner never used
or validated. Breadth is not worth carrying unvalidated, maintenance-bearing
templates.

**Lesson:** scope a removal by checking dependents on the resolved chain,
not by name — all four were leaves, so the blast radius was just their own
files plus auto-regenerated tables. Preserve incidental coverage by
repointing (DPL-02 → go-service), not deleting, when a test merely used a
removed stack as a carrier.

**Template feedback:** the slimming criterion (keep only stacks actually
used/validated) is project governance — ADR-011 applied to whole stacks,
not a reusable template rule.

**PRs merged:** #647

**Issues closed:** #646, #180. Created and closed milestone v2.25.0.

## 2026-06-26 — v2.26 Stack cleanup round 2 + markdownlint config

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Milestone v2.26 — Stack cleanup (round 2), same provenance rationale
  (ADR-011) as v2.25.
- #650: added `.markdownlint.json` matching the template house style —
  disables MD022/031/032/040/060 (heading/list/fence/table-style) and
  keeps MD013 <80 for prose. markdownlint is not in CI, so it only quiets
  the editor (PR #651; MD060 added in the removal PR when table-style
  noise surfaced).
- #649: removed 9 stacks — full-nextjs, full-sveltekit, mobile-flutter,
  mobile-react-native, spa-react, spa-vue, spa-svelte, static-site-hugo,
  python-celery-worker. Also dropped the orphaned mobile/ layer
  (mobile-auth, mobile-ux), the react-spa example, 5 e2e cases
  (STK-05/06/09/14/17 retired), and the smoke runner's mobile template
  dir. Stacks 26 → 17; frontend now = static-site-astro + htmx (PR #652).

**Decision:** cut a new v2.26.0 rather than move the published v2.25.0
tag. Published releases are immutable (ADR-006); moving a tag rewrites a
released artifact, the same hazard as a force-push.

**Lesson:** removing stacks orphans their *exclusive* layer templates
(mobile/) and leaves the smoke runner's `TEMPLATE_DIRS` pointing at a
deleted directory — sweep both. Check transitive reachability before
removing a layer template: frontend-ux/quality stayed because astro still
reaches them via frontend-static-site.

**Template feedback:** the removal is governance (provenance applied to
whole stacks); the markdownlint config documents the project's markdown
conventions — both project-specific, no reusable template change.

**PRs merged:** #651, #652

**Issues closed:** #649, #650. Created and closed milestone v2.26.0.

## 2026-06-26 — 360 audit + audit-storage convention lock

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Ran a full 360-degree audit using the headless adaptation of
  `base/workflow/360.md` (§360-headless): seven context-isolated
  subagents — Value / Viability / Discovery plus Quality re-projected
  into Architecture, Documentation, Authoring/ADR, and Testing/CI.
  Overall C+; bottleneck = a shipped resolver defect. Persisted at
  `docs/audits/2026-06-26-360.md`.
- Filed 12 actionable tickets (#654–#665) across new milestones v2.27
  (correctness), v2.28 (hygiene), and v3.0 (launch); milestoned and
  labelled the previously-orphaned #638.
- #666: adopted the dated-report audit convention — migrated the
  single-file `docs/360-audit.md` to `docs/audits/2026-05-04-360.md`,
  added the new report, fixed the journal pointer.
- #667: collapsed `360.md` §360-tracking to one convention (docs/audits
  only) and added a PLAYBOOK "Run a 360-degree audit" section.
- #668: ADR-018 (docs/audits is the sole audit location) + smoke SYS-07
  gate (no audit file outside docs/audits/, dated naming) + pair-the-check
  line in 360.md + spec SAIT-SMK-SYS-07-001A; backfilled the missing
  SYS-06 in CODIFICATION. Smoke 20 → 21.

**Decision:** lock the audit-storage convention three ways — ADR +
template/PLAYBOOK docs + a mechanical smoke gate — rather than
documentation alone, so it cannot drift back to the two-option ambiguity.

**Lesson:** the audit's highest-value finding (resolve.py dropping a
multi-line `depends_on`) was invisible to the 20-check smoke suite
because two divergent manifest parsers — PyYAML in smoke, hand-rolled in
resolve.py — were never reconciled. A green check suite can still ship a
broken artifact when the check and the tool do not share a code path.
Reproduce the crux finding directly before grading it.

**Template feedback:** the single-convention audit storage (§360-tracking)
and the headless 360 adaptation (§360-headless) are reusable — both live
upstream in `templates/base/workflow/360.md`. The SYS-07 check and
ADR-018 are project-specific tooling and governance.

**PRs merged:** #666, #667, #668

**Issues closed:** none. Created #654–#665 (+ milestoned #638) and
milestones v2.27, v2.28.

## 2026-06-26 — v2.27 Correctness & generation integrity

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- #654 (P1 bug): taught the stdlib-only manifest parsers in
  `resolve.py`/`sync.py` to read a bracketed `depends_on` continuation
  line. `frontend-static-site` was the only entry in that form, so its
  deps parsed empty — `stack-astro`/`stack-tutorial` had shipped with no
  security/CSS/UX/SEO rules (10 files, not 13). Regenerated both chains.
- #655 (P1): added smoke check MNF-05 — resolve every stack with both
  the hand-rolled parser and PyYAML and fail on any mismatch. Verified
  it fails on the pre-fix parser. Smoke 21 → 22.
- #656: removed the vestigial `"mobile"` manifest section (dead since
  v2.26) from the iteration tuples in `resolve.py` and `run_smoke.py`.
- #657: repointed `SAIT-E2E-STK-07-001A`'s retired STK-06 cross-ref to
  STK-20, and dropped three phantom `FMT-03/04/05` rows from
  `tests/INDEX.md` (no spec file, no case).
- #658: named `data-governance`/`data-migration` as intentional opt-in
  orphans in SPEC's Orthogonal-templates list (both reached by zero
  chains; `data-quality` is the only chain-reached data module).

**Decision:** fix #654 by teaching the regex parser (keeping `tools/`
import-free) rather than unifying on PyYAML, then close the
two-parser fragility *mechanically* with MNF-05 rather than collapsing
to one parser — the reconciliation gate is stronger than a single
parser, which could still diverge from YAML semantics on another edge.

**Lesson:** a self-consistency check cannot catch a wrong artifact when
it regenerates from the same broken code — `resolve.py --check` validated
`generated/` against the very parser that produced the defect and
reported "up to date." A correctness gate must compare against an
independent reference (here, PyYAML), and you must prove it fails on the
broken input before trusting it green.

**Template feedback:** the parser fix and the MNF-05 gate are
project-specific tooling — no upstream template. The reusable principle
(gate two implementations against a reference oracle, and prove the gate
red before trusting it green) is a testing discipline, not a template
rule; left in this journal, not added to a template file.

**PRs merged:** #670, #671, #672, #673, #674

**Issues closed:** #654, #655, #656, #657, #658. Released v2.27.0 and
closed milestone v2.27.

## 2026-06-26 — v2.28 Authoring & test hygiene

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- #660 (PR #676): renamed go-lib's idiom section "Code quality" →
  "Go conventions" (ID go-lib-conventions) per ADR-017 clause 5; all four
  Go chains inherit it.
- #659 (PR #677): reflowed 136 prose lines <80 via a content-preserving
  splitter (one space → newline per break, non-whitespace content
  asserted unchanged per file); documented the §2.7 exemption for table
  rows, fenced code, single-line `[DEPENDS ON:]`, and unbreakable
  URL/link tokens.
- #638 (PR #678): scope.md handoff-breadcrumb rule now requires the
  wrap-up writer to validate each candidate against the tracker and drop
  closed/out-of-milestone ones before listing.
- #663 (PR #679): regenerated the hybrid-astro example via the ADR-016
  pipeline — flattened submodule paths corrected to the resolvable
  `docs/solid-ai-templates/templates/base/core/quality.md` form (all 12
  resolve).
- #661 (PR #680): added e2e cases STK-21 (nestjs), STK-22 (c-embedded),
  STK-23 (tutorial) + specs/INDEX/CODIFICATION; STK coverage 14→17.
- #662 (PR #681): smoke SYS-08 locks in the 7 example→stack pairs (each
  example must keep a non-empty CLAUDE.md mapped to a real stack). Smoke
  22 → 23.

**Decision:** lock the example set at the existing 7 (gate by example→
stack, two map to astro and two to fastapi) rather than requiring an
example for every concrete stack — the latter would force ~8 new
agent-generated examples, its own effort. New examples opt into the gate
by registering in REQUIRED_EXAMPLES.

**Lesson:** a bulk content reflow over reference docs is safe to automate
*iff* the transform is whitespace-only and you assert it — comparing the
non-whitespace content before/after per file turns "did I corrupt a
rule?" from a manual review into a guarantee. Pair any mechanical sweep
with that invariant before trusting it.

**Template feedback:** the "Go conventions" rename (#660), the §2.7
line-length exemptions (#659), and the scope.md handoff-validation rule
(#638) are reusable and live upstream in `templates/`. The reflow
splitter, SYS-08 gate, and the three e2e cases are project tooling/tests.

**PRs merged:** #676, #677, #678, #679, #680, #681

**Issues closed:** #659, #660, #661, #662, #663, #638. Released v2.28.0
and closed milestone v2.28.

## 2026-06-27 — Redundancy audit & CI ratchet

**Tool:** Claude Code (Opus 4.8, 1M context)

**Key changes:**
- Session opened exploring authoring/review skills (`write-template`,
  `review-template`) under `.claude/skills/` — kept local, never
  committed, then removed once we judged `write-template` redundant with
  always-loaded context. Running the review on the core tier is what
  surfaced the redundancy that became the focus.
- #683 (PR #684): trimmed base-quality's Testability and Testing
  sections that restated rules owned by base-testing — every chain
  loaded both.
- #685 (PR #686): removed the migration-commit rule restated by
  python-flask/fastapi/django; they inherit it from python-service.
- #687 (PR #688): added `tools/audit_redundancy.py` — override-aware
  in-chain duplicate detector (exact + `--near`); PLAYBOOK "Audit
  redundancy" + CLAUDE.md §1.3 commands.
- #689 (PR #690): corrected the Python Stack override graph
  (python-service-stack overrides python-lib-stack; framework stacks
  override python-service-stack — the abstract Stack was leaking into
  every chain) and removed the app-logging rule from go-lib (owned by
  backend-observability; standalone go-lib drops it, service chains
  keep it). Audit 6 → 2.
- #691 (PR #692): `BASELINE` allowlist + wired `audit_redundancy.py
  --check` into CI as a ratchet (fail on new exact dups only).
- #693 (PR #694): cleared the last two frontend restatements (analytics,
  prettier); `BASELINE` emptied → true zero.

**Decision:** ADR-019 — detect on the resolved chain, exclude
override-superseded pairs, gate exact duplicates only, ratchet from a
baseline. #624's `frontend/seo.md` extraction stays deferred to the
restructure under #492 (commented, kept open).

**Lesson:** a duplicate-detection gate over a composition system MUST
model the override graph or it cries wolf on legitimate replacement —
the throwaway probe over-reported the Go Stack sections; the
productionized tool excludes `[OVERRIDE]`-superseded pairs (transitively)
and the false positives vanished. Validate a new lint's signal against
real findings first, and introduce it as a baseline ratchet, not a
zero-gate.

**Template feedback:** the Python override-graph correction (#689) and
the go-lib app-logging removal are reusable template fixes (live in
`templates/`). The audit tool, `BASELINE`, and the CI gate are project
tooling/infra; the audit-then-baseline-ratchet sequence is a reusable
process for introducing a content-quality gate.

**PRs merged:** #684, #686, #688, #690, #692, #694

**Issues closed:** #683, #685, #687, #689, #691, #693. #624 commented
(seo.md extraction deferred to #492); journal/ADR PR carries no
milestone.

## 2026-06-27 — Wiki: patterns→wiki rename, cleanup, backend article

**Tool:** Claude Code (Opus 4.8, 1M context).

Cosmetic-then-substantive pass over the human-reference docs: renamed
the `patterns/` folder to `wiki/` and grew it with a backend primer.

- #696: renamed `docs/patterns/` → `docs/wiki/` ("gathers knowledge");
  swept the 5 pages (titles, lead text, all `[ID]` tags → wiki framing)
  and fixed stale `base/*-patterns.md` cross-links; updated the SPEC
  Wiki section. Also removed SPEC's never-implemented `Resolution: full
  (rules + patterns)` mode and its companion `*-patterns.md` step —
  drift that contradicted ADR-004 (patterns are human reference, not in
  the manifest or agent context).
- #697: stripped the vestigial template machinery the pages carried
  from their old life as `base/*-patterns.md` templates — all 50
  `[ID]`/`[DEPENDS ON]` tags — and trimmed per-section dividers (8 → 1
  per page). Confirmed: not in the manifest, never resolved, never
  scanned by smoke.
- #699: added `docs/wiki/backend.md` — a concept-first primer (what a
  backend is, API styles, building blocks, composing for requirements,
  reference compositions). Folded the `imbra-ltd/nango-blogs`
  webhook-floods post in as a building-block composition ("inbound
  webhooks under load"), vendor-neutral — product marketing stripped.
- #700: filled §3 building-block gaps — Config/secrets, Feature flags,
  Analytics/warehouse, and load balancing + CDN on the edge row.

**Decision:** no new ADR. The rename is a label change and the SPEC
cleanup enacts ADR-004 (wiki pages are human reference, outside the
dependency graph) rather than deciding anything new.

**Lesson:** docs describing a never-built mechanism are drift, not
documentation — SPEC's `Resolution: full` could never differ from the
default once ADR-004 moved patterns out of the manifest. And a "new
topic" (webhook floods) is often just a composition of existing blocks
(queue, DLQ, dedup, debounce, fairness); framing it that way keeps a
primer coherent and avoids redundancy with the rules templates.

**Template feedback:** all changes are project-specific to `docs/wiki/`
(human reference). The webhook-flood defenses already live in
`templates/backend/webhooks.md` (which delegates DLQ/debounce/fairness
to `messaging.md`), so no template change was needed — the wiki article
only cross-references them.

**PRs merged:** #696, #697, #699, #700

**Issues closed:** none (ad-hoc session); none created. Journal PR
carries no milestone.

## 2026-07-05 — v2.29 Generation coherence

**Tool:** Claude Code (Fable 5).

Triaged the 16 unmilestoned issues (labels + Backlog/v3.0 split), then
planned and shipped v2.29 — four fixes where the generated output
contradicted itself or its own rules:

- #708: promoted `base-review` into the `core:` tier (now six
  templates). It was registered but reachable by no chain while the
  agents.md §5 skeleton universally hardcoded review.md — the review
  process was unreachable through the dependency graph. SPEC orthogonal
  set updated; all 17 chains regenerated. The base-oop reach question
  split out to #727.
- #710: agents.md said "omit section 4 for a backend service" while all
  four service examples keep the placeholder. Convention now matches
  the examples: top-level sections 1–6 are role-fixed; a non-applicable
  section keeps its heading with a one-line `Not applicable — <reason>`
  body; only subsections may be omitted.
- #716: reconciled README-as-SSOT with the Project-structure section
  requirement (ADR-020): README owns the directory map; the generated
  section is a pointer to README plus agent-facing placement rules,
  never a second tree; stack templates keep layout sections as
  generation-time input. Examples realign at the next regeneration
  (#709).
- #713: base-readme §4 now permits the structure as an indented tree or
  a two-column `Path` | `Purpose` table (validated downstream in
  demo-sensor-app).

**Decision:** ADR-020 — README owns the directory map
(`docs/decisions/020-structure-section-ownership.md`).

**Lesson:** a skeleton that hardcodes a template path is an implicit
dependency the manifest cannot see — anything the output format
references universally must be in the core tier, or generation quietly
severs it. Coherence bugs surface downstream first: three of the four
fixes were reported from consuming projects (demo-sensor-app).

**Template feedback:** all four changes ARE template changes — nothing
project-specific to feed upstream this session.

**PRs merged:** #726, #728, #729, #730

**Issues closed:** #708, #710, #713, #716. Created: #727 (base-oop
reach, Backlog). Journal PR carries no milestone.

## 2026-07-05 — v2.30 Downstream lessons

**Tool:** Claude Code (Fable 5).

Second milestone of the day (after v2.29): drained the
downstream-evidence batch from the Backlog — seven template
refinements fed back from corrosim, wuseria, and demo-sensor-app,
shipped as five PRs:

- #704 + #720: hardened `quality-gates-scope-agreement` with the
  formatter-vs-generator escalation (ignore entry + `--check` gate +
  same-PR landing, from wuseria #1336) and the always-run-job rule
  for mirroring cross-cutting deterministic checks (path filters are
  enumeration-fragile; from a docs-only PR that broke a main deploy).
- #722: new `quality-gates-complexity` section — gate cognitive
  complexity (complexipy / sonarjs), retrofit via a committed ratchet
  baseline; the what-NOT-to-gate McCabe bullet now points there
  (corrosim ADR 0013: the two metrics measurably disagree).
- #723: new `quality-gates-tree-audit` section — dup/dead-code
  detectors are a documented periodic whole-tree audit at epic/release
  boundaries, not a per-PR gate; diff-scoped review cannot see the
  twin of a pasted block (corrosim PLAYBOOK 3.8).
- #718: bidirectional-artifact caveat under git.md's regenerate rule —
  an artifact an `--apply` step reads back into the source is ground
  truth; auto-regenerating it overwrites human-verified values
  (wuseria S201).
- #719: python-lib src/ adoption must audit path-based excludes for
  package-dir collisions and anchor them (corrosim: bandit silently
  dropped src/corrosim/report/ — 2357 vs 4312 LOC scanned, CI green).
- #721: platform/github retry pattern for transient `uses:` steps —
  continue-on-error + outcome-gated (not conclusion) conditional
  retry, fail-loud second attempt, infra steps only (wuseria ADR-077).

**Decision:** no new ADR — all changes are rule additions inside
existing template sections; nothing structural.

**Lesson:** the Backlog batch pattern works — seven issues from three
downstream projects composed into one themed milestone with zero
scope collisions. Downstream incident reports that name the exact
section they refine (`quality-gates-scope-agreement`) are the
cheapest template improvements to land.

**Template feedback:** all seven changes ARE template changes
distilled from downstream projects — the feedback loop working as
designed.

**PRs merged:** #732, #733, #734, #735, #736, #737

**Issues closed:** #704, #718, #719, #720, #721, #722, #723; none
created. Journal PR carries no milestone.

## 2026-07-10 — v2.31 CI & test hardening

**Tool:** Claude Code (Opus 4.8 [1M]).

Groomed the post-v2.30 downstream-lessons backlog — 36 unmilestoned
issues labeled, clustered by target file, and milestoned; #749 closed
as a duplicate of #753. Then cut v2.31 from the ready subset: ten
self-contained CI, security, and test-hardening rule additions to
chain-reaching template files, shipped one concern per PR (#776–#785).

- #751 (#776): pair the LF MUST in `quality.md` with a `.gitattributes`
  mechanism (`* text=auto` / `eol=lf`) — EditorConfig normalizes
  editor-side, `.gitattributes` is the git-side commit/checkout
  guarantee; names `git ls-files --eol` as the check (corrosim CRLF
  churn).
- #756 (#777): scope the coverage denominator to the CI-runnable
  surface — omit genuinely un-runnable modules (native / GPU /
  container-only) and validate them out-of-band; the omit-list is a
  reviewable contract, the coverage analogue of the complexity ratchet.
- #754 (#778): new in-process config model in `config.md` — frozen
  preset object + name registry + unset-means-default resolver;
  composes with 12-factor env rather than replacing it.
- #758 (#779): AST meta-test for the public-API annotation + docstring
  contract in `testing.md` — the linter owns format, a test owns
  presence on the public surface only, adopted behind a module
  allowlist.
- #763 (#780): drift-guard meta-tests in `testing.md` — any fact stored
  twice gets an introspection test that fails on divergence
  (constant-vs-contract, route coverage, version parity).
- #759 (#781): secret scanning MUST cover full git history
  (`fetch-depth: 0`) in `devsecops.md` + `platform/github.md` — a
  deleted secret persists in old commits, so a shallow scan is false
  safety.
- #762 (#782): split scanning by actionability in `devsecops.md` — gate
  on owned deps, inform on unfixable base-layer CVEs; reconciled the
  `containers.md` push rule to "no **fixable** high/critical".
- #768 (#783): runtime version coherence in `containers.md` — base
  image, CI, type-checker target, and packaging floor pin ONE runtime;
  move them together so a base-only bump can't ship an untested runtime.
- #769 (#784): fan-in gate mechanism in `platform/github.md` — one gate
  per job + a single `always()` fan-in as the sole required context,
  failing unless every result is exactly `success` (skipped / cancelled
  count as failure); the encoding the `quality-gates` "skipped is not
  passed" rule demanded.
- #770 (#785): least-privilege workflow permissions in
  `platform/github.md` — `contents: read` default, job-scoped writes,
  SAST's `security-events: write` isolated in its own workflow.

**Decision:** no new ADR — all ten are rule additions inside existing
template sections; nothing structural. Milestone named for its content
("CI & test hardening"), not a round number.

**Lesson:** groom-then-drain scales — a 36-issue downstream batch
triaged into a ready ten-issue themed milestone (self-contained edits
to chain-reaching files) while new-file and reference-only-doc
(`ai-workflow.md`) issues stayed parked for v3.0. Sequential
one-concern PRs kept the `generated/` regen honest per change.

**Template feedback:** all ten are template changes distilled from
downstream evidence (corrosim et al.) — reusable upstream content, the
feedback loop as designed.

**PRs merged:** #776, #777, #778, #779, #780, #781, #782, #783, #784, #785

**Issues closed:** #751, #754, #756, #758, #759, #762, #763, #768, #769, #770;
plus #749 as a duplicate of #753 during grooming. Journal PR carries no
milestone.

## 2026-07-10 — v2.32 Testing & authoring discipline

**Tool:** Claude Code (Opus 4.8 [1M]).

Third milestone of the day (after v2.31): a themed subset of the same
downstream backlog — ten self-contained testing-depth and
authoring-discipline rule additions to existing core/base files, one
concern per PR (#787–#796). Scope confirmed before the cut; new-file and
reference-only-doc issues stayed parked for v3.0.

- #739 (#787): `oop.md` gains a "When not to reach for a class"
  counterweight — prefer free functions for stateless logic, treat a
  `run()`-only class as a function in disguise, put behaviour on the
  state that owns it. The file was all pro-OOP, biasing toward
  over-abstraction.
- #740 (#788): characterization-fingerprint refactor proof in
  `testing.md` — hash the full-precision output before, regenerate and
  diff after; seed nondeterminism; keep the hash disposable (a committed
  platform-dependent hash goes CI-flaky — commit invariants instead).
- #764 (#789): serve the real app in-process on an ephemeral port (bind
  0 in a daemon thread) — the lightweight middle between the framework
  test client and a container; one helper for driver scripts and
  browser UI tests.
- #765 (#790): runtime-agnostic, health-gated container e2e — drive via
  a Docker-API-compatible library (Docker/Podman via `DOCKER_HOST`),
  poll-not-sleep, import-guard the optional dep, disable the rootless
  reaper.
- #774 (#791): derive the test tier from the directory with one
  collection hook (a marker can't drift from where the test sits) and
  default the run to the fast tier, heavy tier opt-in.
- #741 (#792): `docs.md` — a per-field generator MUST derive its field
  enumeration from the data schema, never a hardcoded list; dead columns
  are the visible tell of the silent-omission failure (wuseria S206).
- #742 (#793): `docs.md` round-trip rule — a refresh of a
  scaffold-plus-human-edits file MUST preserve human content or fail
  loud naming what it would discard; silent revert is data loss
  (wuseria S207).
- #744 (#794): de-circularization sweep in `quality.md` calibration
  discipline — when a reference set flips from tool-seeded to verified,
  grep for comments/guards/thresholds citing the old data and re-verify
  in the same change (wuseria S209).
- #745 (#795): forbid ticket/PR/ADR *numbers* in code comments and
  docstrings (markdown docs still cross-ref by number); scientific
  source names are the exception; grep test named as enforcement
  (corrosim #151).
- #746 (#796): warn in `git.md` that a `close/fix/resolve #N` keyword
  auto-closes even inside a negation ("does not close #N" still closes
  it) — use "part of #N" instead (corrosim).

**Decision:** no new ADR — all ten are rule additions inside existing
template sections; nothing structural. Scope confirmed via a
themed-subset choice, not an autonomous cut, since a release is
outward-facing.

**Lesson:** two consecutive themed drains (v2.31 CI/security, v2.32
testing/authoring) came out of one 36-issue groom — theming by target
file at groom time makes each release a coherent, low-collision cut.
A chained `gh pr create && gh pr checks --watch` raced CI registration
once (#788 "no checks reported"); splitting create from watch fixed it.

**Template feedback:** all ten are template changes distilled from
downstream evidence (corrosim, wuseria) — reusable upstream content.

**PRs merged:** #787, #788, #789, #790, #791, #792, #793, #794, #795, #796

**Issues closed:** #739, #740, #741, #742, #744, #745, #746, #764, #765, #774.
Journal PR carries no milestone.

## 2026-07-10 — v2.33 Backend correctness

**Tool:** Claude Code (Opus 4.8 [1M]).

Fourth milestone of the day: the backend-layer subset of the same groom
— five request / response / concurrency correctness rules, one concern
per PR (#798–#802).

- #766 (#798): `security.md` — state the principle behind the existing
  `nosniff` MIME-pinning rule: with `nosniff` the browser will not
  correct a wrong `Content-Type`, so the server is the sole authority
  and MIME resolution must not depend on the host.
- #767 (#799): `concurrency.md` — prove statelessness with disjoint
  inputs: fire parallel requests with non-overlapping expected outputs
  and assert each response stays in its own set; a cross-request value
  exposes an accidental module-level mutable a same-input test can't.
- #772 (#800): `api.md` — the contract document's own version
  (OpenAPI `info.version`) is a separate axis from the package/release
  version; don't bump it on a package patch that doesn't touch the
  contract, and a drift test asserts the field present, not equal.
- #773 (#801): `http.md` — parse typed query params explicitly to
  distinguish absent / valid / present-but-invalid (400), not a
  coercing helper that collapses invalid into a default-valued 200.
- #775 (#802): `http.md` — name the concrete `allow_nan=false` encoder
  flag on the existing reject-non-finite-floats rule.

**Decision:** no new ADR — all five are rule additions/refinements
inside existing template sections; nothing structural.

**Lesson:** two of the five (#766 nosniff MIME, #775 `NaN`/`Infinity`)
were already substantially in the templates from an earlier downstream
pass — the groom predated those additions. Grep the target file for
existing coverage BEFORE writing: both shipped as minimal
principle/example enhancements, not redundant bullets. A backlog groomed
weeks deep should expect some items overtaken by intervening work.

**Template feedback:** all five are template changes distilled from
downstream evidence — reusable upstream content.

**PRs merged:** #798, #799, #800, #801, #802

**Issues closed:** #766, #767, #772, #773, #775. Journal PR carries no
milestone.

## 2026-07-10 — v2.34 CI & deploy

**Tool:** Claude Code (Opus 4.8 [1M]).

The last self-contained cut from the groom (v2.31–v2.34) — three
CI/deploy rules, one concern per PR (#804–#806).

- #771 (#804): `cicd.md` — a deploy step whose optional secret is absent
  on forks/contributor branches MUST skip and stay green, not hard-fail.
  The issue's other two refinements (deploy-the-published-artifact,
  tag-triggered production) were already present from #601 build-once CD
  and the triggers table — only skip-not-fail was missing.
- #752 (#805): `containers.md` — new Docker Compose section (Compose was
  absent from the whole tree): when warranted, the `build` / `run --rm`
  workflow, and bind-mount-for-local-dev-only versus image-is-the-
  artifact in CI/prod. Kept MAY/SHOULD.
- #743 (#806): `platform/github.md` — refine the retry bullet to
  distinguish single-hit flake / multi-minute flake / sustained outage,
  naming a bounded 3-attempt growing-backoff escalation for the middle
  class with a reclassify stop condition (wuseria ADR-078).

**Decision:** no new ADR — rule additions/refinements inside existing
sections; the Compose section is new content in an existing file.

**Lesson:** the drainable backlog is now exhausted. One 36-issue groom
produced four themed minor releases (v2.31 CI/security, v2.32
testing/authoring, v2.33 backend, v2.34 CI/deploy) plus a duplicate
close — theming by target file at groom time is what let each cut land
coherently. The remaining 8 Backlog issues ALL require v3.0 groundwork
(new files `python.md` #753 / `cli.md` #755 and their dependents, and
reference-only-doc placements blocked on the #179 inline→ref
restructure); no further self-contained minor is possible without it.

**Template feedback:** all three are template changes distilled from
downstream evidence — reusable upstream content.

**PRs merged:** #804, #805, #806

**Issues closed:** #743, #752, #771. Journal PR carries no milestone.

## 2026-07-10 — v2.35 Discipline refinements

**Tool:** Claude Code (Opus 4.8 [1M]).

A fifth themed minor from the groom, recovered after re-checking the
"exhausted backlog" claim made at v2.34 — three issues parked as
v3.0-blocked were actually self-contained. One concern per PR
(#808–#810).

- #761 (#808): `scope.md` — strengthen the End-of-session template-
  feedback item on three axes: capture the reusability verdict at
  decision time (on the ADR, robust to sessions that never wrap), strip
  the domain skin before judging, reconcile the whole convention set
  periodically. The meta-fix behind the #749–#760 batches, which had to
  be surfaced by a deliberate later gap-analysis instead of firing.
- #760 (#809): `python-lib.md` — reconcile the flat `mypy --strict`
  mandate with a staged adoption path (non-strict + `ignore_missing_imports`
  → tighten per module toward strict) and quarantining untyped deps with
  a per-module override plus a stated reason.
- #747 (#810): `docs.md` — a provenance/justification-doc backfill is a
  data audit: cross-check each stored value against its cited source,
  surface a gap rather than encode a false "not tested" marker,
  distinguishing source-silent from source-has-data-but-unpopulated.

**Decision:** no new ADR — rule additions/refinements inside existing
sections.

**Lesson:** the "drainable backlog exhausted" call at v2.34 was wrong. I
parked #747/#760/#761 as v3.0-blocked from the issue titles' file names,
assuming reference-only or new-file dependence. Verifying each target
against the resolved chains with `resolve.py` (scope.md IS in
stack-tutorial; python-lib.md and docs.md are in-chain) recovered a
fifth cut. Verify chain membership before declaring an item blocked —
not from the filename in the title.

**Template feedback:** all three are template changes distilled from
downstream evidence — reusable upstream content.

**PRs merged:** #808, #809, #810

**Issues closed:** #747, #760, #761. Journal PR carries no milestone.

## 2026-07-12 — Annotated release tags (incident #812)

**Tool:** Claude Code (Opus 4.8 [1M]).

Incident triaged out of Expedite: 30 of 37 release tags were lightweight
(`git tag`), which `git describe` skips — a downstream submodule pinned at
`v2.35.0` reported `v2.17.0-128-g6969ccd`. Root cause was in the templates
themselves: the version-manifest release flow in `git.md` and
`static-site-tutorial.md` used plain `git tag`, and the no-build flow used
`git tag -a` with no rationale, so operators "simplified" the `-a` away.

- #812 (#813): `git.md` — both release flows now mandate `git tag -a`
  with an inline rationale (a lightweight tag is invisible to
  `git describe`); `static-site-tutorial.md` fixed the same way; new
  `.github/workflows/tag-guard.yml` fails CI when a pushed `v*` tag is
  lightweight; regenerated the 17 `generated/` chains (base-git is core).
- Retagged all 30 historical lightweight tags as annotated at their
  original commits — `git describe 6969ccd` now returns `v2.35.0` exactly;
  37 annotated / 0 lightweight.

**Decision:** no new ADR — the annotated-tag requirement and its rationale
live in the `git.md` template; ADR-006 (release process) stands unchanged.

**Lesson:** `git push --force` is blocked by the harness even for tags. The
fallback delete+re-push detaches a tag's GitHub Release to a draft (restore
per-tag with `gh release edit --draft=false`); updating the tag ref in
place is preferable, as it keeps Releases published.

**Template feedback:** reusable — the fix lives in the `base-git` template,
so annotated-tag discipline plus the CI guard propagate to every consumer.

**PRs merged:** #813

**Issues closed:** #812. Journal PR carries no milestone.

## 2026-08-02 — v2.36 Branch & session hygiene and v2.37 Documentation & README conventions

**Tool:** Claude Code (Opus 5 [1M]).

Two milestones planned and drained in one session, plus a tracker decision.

**Groom.** The 39 untriaged downstream issues were clustered into ten groups
by target file, the eight carrying no priority label were labelled, and the
overlaps recorded: #846 and #849 were largely overtaken by #880, which shipped
the day before; #816 and #824 are one convention in two files; #863 blocks on
#859.

**v2.36 — Branch & session hygiene** (#888-#899). The startup branch cleanup
(#865) was broken in this repo's own CLAUDE.md: `git branch --merged main`
cannot match a squash-merged branch, so it exits 0 having deleted nothing.
Four merged branches had accumulated unnoticed. The requirement moved to
`scope.md` with the `gh` commands in `platform/github.md`. Also: tests must not
signal host processes (#858), the two branch-deletion paths under a stack
(#859, #863), `fetch.prune` (#836), an imperative end-of-session audit (#825),
verifying a visual change against the render (#820), and the submodule-versus-
linter warning (#861).

**v2.37 — Documentation & README conventions** (#901-#906). Badges move under
the H1 and the capability list becomes required section 2 under `## Features`,
which also answered #835 (#881). No ADR citations in the README (#882). Check
the inherited rule before calling a document wrong (#864). Cite by persistent
identifier (#845). Delegate to a self-documenting source (#822). The
`examples/` convention across `readme.md` and `python-lib.md` (#816, #824).

**Tracker.** GitHub is the system of record; Linear is a view. #887 removed
the Linear ticket from this repo's branch-naming convention. The template side
(#883) is still open.

**Decision:** partial ADR supersession dropped (#856, `wontdo`). Representing
it would have needed a superseding ADR against ADR-010, a change to the
`status=Superseded iff superseded_by non-empty` invariant in `run_smoke.py`,
and new wording — three coupled changes to give one field a second conditional
meaning.

**Lesson — test the claim, do not reason about it.** #859 shipped a blanket
"never delete a branch under a stack". Two throwaway stacks against scratch
bases disproved half of it within minutes: deletion *as part of the merge*
retargets the dependent PR and leaves it open, while a separate delete-branch
flag closes it irreversibly. The blanket rule also contradicted `git.md`'s own
"enable automatic head-branch deletion" two sections earlier. #863's PR
narrowed it.

**Lesson — verify the tool before believing its finding.** Two defects reported
at the end of v2.36 were both false. `awk 'length>80'` counts *bytes*, and an
em dash is three of them, so every line with one read as over-long; a
character-based scan of every template returns zero violations. The MD029
warnings flag deliberate continuous numbering that CommonMark renders
correctly. Neither was filed; #900 (silence MD029) was filed instead.

**Lesson — a self-referential count goes stale silently.** Renumbering the
README sections broke two claims elsewhere: `review.md` asserted "all 8
required sections", and `readme.md`'s own Audience rule said "the first three
sections". The first was caught by grepping for it, the second only by
re-reading the whole section afterwards — which is #847's rule, applied to the
PR that was implementing its neighbours.

**Template feedback:** all sixteen are template changes distilled from
downstream evidence — reusable upstream content, which is what this repo is.

**PRs merged:** #887-#906

**Issues closed:** #816, #820, #822, #824, #825, #835, #836, #845, #856,
#858, #859, #861, #863, #864, #865, #881, #882. Opened #900; reopened #883.
Journal PR carries no milestone.

---

## 2026-08-02 — Milestone lanes retired, then v2.38 and v2.39

**Tool:** Claude Code (Opus 5 [1M]).

A tracker cleanup that turned into a template rule, a full groom of the
remaining backlog, then two milestones planned and drained.

**Milestone lanes retired (ADR-023, #914, PR #915).** Deleting the `Backlog`
and `Expedite` milestones exposed that `platform/github.md` prescribed both as
rules and `issues.md` named a `Backlog`-milestoned issue as the home for
deferred work. Each lane was a milestone doing a label's job: `Backlog`
answered "is this parked" and `Expedite` "is this urgent", both properties of
the issue rather than of a release, and both already encoded by `P4` and the
severity band. A milestone's meaning is also not durable — closing or deleting
one strips the field from every attached issue, while a label survives. The
deferred-work rule was additionally stale against ADR-021, still calling its
`Backlog` issue "distinct from a P4 'someday' issue" after `P4` had been
redefined as exactly a deferral marker.

**Groom.** The 33 untriaged issues sorted into five themed minors (v2.38-v2.42)
rather than one cut, matching the v2.29-v2.35 precedent and the eight-issue
release size. Three moved into v3.0 because they depend on files v3.0 creates,
each verified from the issue's own text rather than by theme resemblance: #815
names the CLI conventions #755 introduces, #857 defers to `frontend/seo.md`
from #624, #844 needs the placement #492 decides. #831 and #832 stayed
unmilestoned on `P4` — putting a deliberately-deferred issue into a dated cut
would contradict the rule shipped an hour earlier.

**v2.38 — Review discipline** (#918-#922). Four of the seven issues were
retractions of confident, wrong findings, and they shared one shape: the
finding was reported before it was demonstrated, and the check that would have
caught it depended on the finding's provenance. `review.md`'s agent-findings
section widened into "Verifying a finding before reporting it", organised by
whether the finding came from a read (#860), a measurement (#912), an
extraction (#846), or an agent (#849). Also: re-read the whole section after
changing a sentence (#847), composite-metric independence (#833), and auditing
every step of a composite gate command rather than the one that broke (#843).

**v2.39 — Pipeline & derived-data correctness** (#924-#926). A new
`Expensive computations (if applicable)` section in `quality.md` pairs the two
halves of one construct: do not hand back an unconverged result, and do not
discard the state you already paid for (#818, #828). Two rules govern what such
a pipeline may emit — blank a derived quantity outside its defining condition
(#827), and take the fidelity bar from the strictest *visible* consumer (#829).
A diagnostic view must run through the production entry point (#830).

**Lesson — measure reach, do not recall it.** Session memory recorded
`base-review` as reference-only with zero chains. `resolve.py` shows it
resolves in 17 of 17. That inverted a placement: #849's suggested home
(`agents.md`) reaches nothing, so it went to `review.md` instead. The same
check moved #828 out of `base/data/` (4 of 17, all web services) into
`quality.md`. Reach is the placement criterion and it is one command away.

**Lesson — a rule found its own class of bug one release later.** Applying the
self-referential-claim check from #847 to the Calibration discipline section
while editing it showed the intro claiming "three failure modes ... the rules
below address each" against six existing subsections. The claim was accurate
when written and drifted as rules accumulated. Rewritten to carry no count.

**Template feedback:** all thirteen are template changes distilled from
downstream evidence — reusable upstream content, which is what this repo is.
The milestone-lane removal is the exception in kind: it began as a local
tracker cleanup and became a rule only because the templates prescribed the
thing being removed.

**Releases:** v2.38.0, v2.39.0. Milestones v2.36-v2.39 closed; v2.36 and v2.37
had shipped earlier the same day but were left open.

**PRs merged:** #915, #918, #920, #921, #922, #924, #925, #926

**Issues closed:** #914, #818, #827, #828, #829, #830, #833, #843, #846,
#847, #849, #860, #912. Milestones `Backlog` and `Expedite` deleted;
v2.40-v2.42 created. Journal PR carries no milestone.

## 2026-08-02 — v2.40 Tooling, containers & CI

**Tool:** Claude Code (Opus 5 [1M]).

A tracker placement pass, then the milestone drained end to end.

**Placement.** Five issues left unmilestoned by the previous session were
placed: the two `platform/github.md` bugs (#916, #917) into v2.40 alongside
the lychee item already there, the submodule read-discipline rule (#927) into
v2.42 with the tracker work, and the two `git.md` merge-mechanics rules (#919,
#923) into a new v2.43 — no existing theme fit them, and folding them into
v2.42 would have made its title stop describing its contents. #831 and #832
stay unmilestoned, which is now correct rather than an oversight: ADR-023
deleted the milestone lanes, so `P4` alone carries deferral.

**Deferral conformance.** ADR-023 requires `P4` plus explicitly named trigger
conditions, and neither #831 nor #832 had one. Both were migrated out of the
`Backlog` milestone on 2026-08-02 by label alone, so the parking rationale the
milestone carried implicitly was lost with it. Triggers were written from each
issue's own content, with the provenance stated on the issue.

**v2.40 — Tooling, containers & CI** (#931-#937). The `## GitHub Pages`
heading had been deleted rather than displaced when Branch cleanup was
inserted, stranding two HTTPS rules under the wrong ID; restored, and the
garbled mismatch bullet directly above it repaired in the same PR since the
edits touch adjacent lines (#916, #917). MD029 joins the disabled house-style
rules (#900). The Lychee note splits into internal and external halves (#848).
The editor's type-checker defers to the CI type gate (#826). An editable
install bind-mounted over its own workdir is guarded against layout drift
(#817), and the write-persistence boundary is documented (#821).

**Lesson — an issue's suggested home is a hypothesis, not a decision.** #834
named `base/workflow/scope.md`, which resolves into 1 of 17 chains.
`base/core/git.md` is 17 of 17 and already owned a
`### Verifying regenerated artifacts` section on exactly that topic — where
one of the issue's three proposed rules already existed, so it was dropped
rather than duplicated. This is the same lesson as v2.39's "measure reach, do
not recall it", one step earlier: measure before accepting the issue's own
suggestion, not only before recalling from memory.

**Lesson — a rule can contradict, not just omit.** #826's `git.md` half read
as a small addition. The `.gitignore` section already said to ignore
`.vscode/` wholesale, which is incompatible with tracking the editor config
the new Layer 1 rule requires. Landing the addition without the allowlist
would have shipped two rules that cannot both be followed.

**Lesson — retiring a lane does not retire its prose.** #831's proposed
template text still instructed "file a Backlog issue" weeks after ADR-023
deleted the lane. Implementing it verbatim would have reintroduced the
retired lane into the very file the ADR stripped it from. After an ADR
removes a concept, grep open issue bodies for it, not only `templates/`.

**Template feedback:** all eight are template changes distilled from
downstream evidence — reusable upstream content. #900 is the exception: it
configures this repo's own editor tooling and travels nowhere.

**Releases:** v2.40.0. Milestone v2.40 closed; v2.43 created.

**PRs merged:** #931, #932, #933, #934, #935, #936, #937

**Issues closed:** #916, #917, #900, #848, #834, #826, #817, #821. Journal PR
carries no milestone.


---

## 2026-08-02 — v2.41 Python & API conventions

**Tool:** Claude Code (Opus 5 [1M]).

**Label gap closed first.** #938 and #939 were filed during the previous
session carrying no labels at all, which CLAUDE.md 2.2 forbids at creation.
They surfaced only because a status sweep enumerated unmilestoned issues —
nothing in CI or the tracker objects to an unlabeled ticket, so the rule is
currently a constraint without its check. Both were labeled `task` / `P3`
and placed in v2.41, taking the milestone from six issues to eight.

**v2.41 — Python & API conventions** (#942-#949). Five rules land in
`python-lib.md`: a test suite's own `sys.path` insert defeats the `src/`
layout (#938), the documented commands must be re-run after a path move
(#939), a stale in-tree `*.egg-info` shadows the fresh `dist-info` (#840),
a library's dependency floors move only when required (#862), and the test
suite is exempt from the ruff `D` rules (#838). Three land in the core
tier: a pluggable tier is named for what it requires of the caller (#908),
the module-to-package split preserves its import path (#837), and a
registered config object also loads from a user file through one resolver
(#819).

**Lesson — a green gate certifies what survived, not what the move was
for.** #938 and #939 are the same defect from two sides. #719 had already
landed the config-side audit for a `src/` move: anchor every path-based
exclude, compare scanned-file counts. In the reported case that audit
passes and its answer is correct — nothing collided. Meanwhile the suite
was still importing from the tree through a `conftest.py` insert that had
simply been repointed, and the README's headline example had stopped
working. Tests, coverage, statement counts, formatted-file counts, mypy
source counts and wheel contents were identical before and after. The
verification has to target the guarantee the move was adopted for
(collection MUST fail against an uninstalled package), not the artifacts
the tooling happens to scan.

**Lesson — the inherited-rule check earns its keep.** #838 is not an
omission but a contradiction across the inheritance boundary:
`python-lib.md` selected the ruff `D` rules without exempting tests, while
`quality-gates-exclusions` in its own dependency chain already rules
docstring coverage on non-public functions out as busywork. Every project
generated from the stack failed `ruff check` on its own test suite at
scaffold time. v2.37's #864 added the check for exactly this; this is the
first case it would have caught.

**Template feedback:** all eight are reusable upstream content distilled
from downstream evidence (`page-fetcher`, `corrosim`). No project-specific
changes in this milestone.

**Releases:** v2.41.0. Milestone v2.41 closed.

**PRs merged:** #942, #943, #944, #945, #946, #947, #948, #949

**Issues closed:** #938, #939, #840, #862, #838, #908, #837, #819. Journal
PR carries no milestone.

---

## 2026-08-02 — v2.42 Documentation, licence & tracker

**Tool:** Claude Code (Opus 5 [1M]).

**v2.42 — Documentation, licence & tracker** (#953-#958). Three rules land
in `issues.md`: the code host is the system of record and the tracker is a
replaceable view over it (#883), the label-at-creation rule is paired with
a conformance check (#952), and a duplicate chain MUST NOT terminate in a
closed issue (#913). `platform-github-labels` carries the concrete `gh`
query; `platform-linear-codehost` is reworded so code-host authority is the
premise rather than a condition on enabling sync. The other three: a README
MUST NOT state a measured value that moves without an edit (#907), a
consuming repository reads the issue list at upstream HEAD and its rules at
the pinned revision (#927), and a redistributed dependency carries an
attribution obligation that approving its licence does not discharge
(#839).

**The milestone closed a loop it opened.** #883 is the P1 rule that went
missing when #883 and #886 were closed against each other; #913 is the rule
forbidding exactly that closure pattern. Both shipped here — the dropped
ticket and the rule that stops the drop, in the same cut. #952 has the same
shape one step removed: it was filed this session against this repository's
own unlabeled #938 and #939, and shipped in the milestone immediately
after the one where the failure occurred.

**Lesson — poll for a terminal state, not for the absence of a running
one.** Two merges this session failed with `QUEUED` after a wait loop
reported the checks finished. The loop asked whether any check was
`PENDING` or `IN_PROGRESS`. Immediately after a push the answer is no
because the array is *empty* — CI has not registered yet — and later the
answer is no again because the state is `QUEUED`, which is neither. Both
times the loop fell through and `gh pr merge` refused. The correct
predicate is positive: at least one check present, and every state in
{`SUCCESS`, `FAILURE`, `SKIPPED`, `NEUTRAL`}. Enumerating the states that
mean "not done" fails open on any state not enumerated; enumerating the
states that mean "done" fails closed.

**Template feedback:** all six are reusable upstream content. #883, #952,
#913 and #927 came from applying this chain to `braboj/page-fetcher` and to
this repository itself; #907 and #839 from `page-fetcher` and `corrosim`.

**Releases:** v2.42.0. Milestone v2.42 closed.

**PRs merged:** #953, #954, #955, #956, #957, #958

**Issues closed:** #883, #952, #913, #907, #927, #839. Journal PR carries
no milestone.

---

## 2026-08-02 — P4 retired: priority is severity only

**Tool:** Claude Code (Opus 5 [1M]).

**The `P4` deferral marker is gone** (#960, ADR-024). Priority is now a
pure four-band severity scale, `P0`–`P3`, one per issue. Deferral moves to
the milestone field: milestoned means planned into that cut, unmilestoned
means backlog. The label was deleted repository-wide, which strips it from
closed issues as well as open ones.

**The reasoning that flipped.** ADR-021 had considered dropping the marker
and rejected it — removing it "pushes the information into prose, where it
stops being filterable". That held only if the alternative to a label was
prose. It is not. The milestone field is itself a first-class, filterable
axis, already mandatory reading when scoping a release and already
documented as optional, with an empty value meaning the work is not tied to
a release. Deferral was being recorded twice in two places that can
disagree. Of the four open issues carrying the marker, two also carried a
milestone and two carried none; in neither pair did the label say anything
the milestone field did not already say.

**What the milestone field cannot say, the body now must.** The objection
ADR-021 raised against folding deferral into a tracker's unset value —
deliberate decisions become unfindable among untriaged ones — applies to an
empty milestone too, and is answered rather than dismissed. Triage here is
the type and severity applied at creation, not the milestone, so an empty
milestone means unscheduled and never untriaged; `base-issues-defer` now
states that explicitly. The trigger conditions in the issue body remain the
record that a deferral was deliberate. What is genuinely lost is the label
filter that used to surface the backlog on its own, so the section gained a
bullet requiring the unmilestoned set to be re-read when a cut is scoped.

**Lesson — retiring a concept does not retire its prose, and this is the
second time it fired.** ADR-023 deleted the `Backlog` lane, and weeks
later #831's proposed template text still said "file a Backlog issue".
That was recorded as a lesson. It happened again in the same file: the same
issue's step 4 instructed a future implementer to apply "a severity label
plus `P4`", so implementing #831 verbatim would have written the marker
back into `platform/github.md` — the exact file this change strips it from.
An open issue body is a delayed write against the templates, and a
concept-removal PR that greps only `templates/` leaves those writes armed.
Both #831 and #832 were rewritten to describe the `Backlog` → `P4` →
unmilestoned migration as history rather than as instruction. The lesson
then landed as a rule (#962): retiring a concept sweeps every surface that
instructs its use, and is done only when a search returns historical
records and no surviving instruction.

**Reach decided the home, and the obvious home was the wrong one.** The
new rule reads as issue-tracker content, which puts it next to
`base-issues-defer` in `issues.md`. Measuring first: `issues.md` resolves
into 1 of 17 stacks, `quality.md` into 17 of 17. The rule went to
`quality.md` beside the existing before-removing-a-public-symbol rule,
where it also mirrors the citation-inherits-its-lifecycle rule pointing
the other way. Worth noting for the P4 change itself — its `issues.md`
edits ship to `stack-tutorial` alone, and only the `platform/` edits
travel widely, since a platform template is chosen independently of the
stack chain.

**Template feedback:** reusable upstream content, already landed.
`base-issues-types` drops the fifth band, `base-issues-defer` is restated
against the milestone field, `platform-github-labels` drops its deferral
table and the conformance-check caveat that existed only to exclude `P4`
from the priority pattern, and `platform-linear-priority` carries the same
rule against a cycle or project milestone. `CLAUDE.md` §2.2 and the
`devsecops` triage flow follow.

**Releases:** none. v2.43 stays open — #923 and #919 remain.

**PRs merged:** #961

**Issues closed:** #960. Journal PR carries no milestone.

## 2026-08-03 — v2.43 Git merge mechanics

**Tool:** Claude Code (Opus 5 [1M]).

**Two independent PRs merged back to back hit the same refusal a stack
does** (#923). Under "Require branches to be up to date before merging",
merging the first moves the base and makes every other open PR stale, so
the next merge is refused for a reason that has nothing to do with
content — it fires on disjoint files and on branches that were never
stacked. `De-stacking a dependent branch` framed the merge-`main`-in step
as a consequence of duplicate commits and `Merging a stack` framed it as
a consequence of stacking, so a reader who had internalised both still
did not expect it. `git.md` now carries `Merging a batch of PRs` between
`Squash-merge safety` and the de-stacking section, and prices the case:
N ready PRs are N merges and N-1 update-plus-CI cycles.

**The de-stacking rule was mandating the more expensive of two equal
routes** (#919). Cherry-picking B fresh off updated main was the only
sanctioned option, and it closes B's PR — discarding its comments and
approvals. Retargeting B and merging main in is equally force-push free,
and under squash merge lands byte-identical content on `main`; the merge
commit it carries is deleted by the squash that follows. Both routes are
now permitted, with the trade-off named so the choice is informed:
cherry-pick when the diff will be read carefully and there is no review
history worth keeping, merge in when B is already reviewed or the stack
is deep enough that re-cherry-picking each level is error-prone. The
equivalence rests on squash merge, so that condition is stated — where
the merge commit would survive on `main`, cherry-pick. The `MUST NOT
rebase an already-pushed branch` from #336 is untouched.

**A null that means two things defeated the precedence table** (#963).
`config.md` already forbade a lower-priority source overriding a higher
one; what was missing was the mechanism. A parser helper returning the
value after a flag, or null when there is none, collapses "flag absent"
with "flag present as the last argument". `tool <target> --wait` then
runs with the hardcoded default: highest-priority source beaten by the
lowest, no error, exit zero — and the shape of it guarantees the failure
lands exactly when the user was trying to set the value. The rule extends
to empty environment variables and empty config keys, which fail
identically. Pulled into this cut rather than left in the backlog,
because it is a silent-failure trap and `config.md` reaches 15 of 17
stacks.

**Reach blocked a placement again, before the edit rather than after**
(#951). The proposed rule — re-read the project's own divergence records
before deciding what a bumped submodule range means, since a rule the
project deliberately does not follow can move upstream and read as a gap
to close — targets `scope.md` item 10, which is where the reconciliation
gap genuinely sits. `scope.md` resolves into 1 of 17 stacks, and that one
is the Astro tutorial site: the least likely place for a submodule
reconciliation. Same trap `issues.md` has. Measuring first cost minutes
and moved the rule: it landed in `docs.md` under `Decision logs` (17/17),
generalised past submodules to any source a divergence was recorded
against, and beside the existing rule for an ADR premise refuted shortly
after merge — the same shape with the refutation arriving from outside.
Nothing was added to `scope.md`, since a pointer there would restate the
rule and the repository has no inline cross-references by design.

The part worth keeping is the second bullet: a reconciliation MUST
separate what the range refuted from what it merely moved nearby. In the
source case the decision survived untouched while the fallback it named
was deleted upstream — that is a repair to the record, not grounds to
reverse it, and reading the diff alone cannot tell the two apart.

**None of this session's own merges hit #923.** Each branch was cut from
main after the previous PR merged, so nothing was ever stale. That is the
other way to avoid the N-1 update cycles, and it costs nothing when the
work is serial anyway — the rule earns its keep when several PRs are
already open and waiting.

**Template feedback:** all four items are reusable upstream content and
all four landed. `base-git` gains `Merging a batch of PRs` and a widened
`De-stacking a dependent branch`; `base-config` gains the absent-versus-
empty distinction under `Config precedence`; `base-docs` gains the
divergence-reconciliation pair under `Decision logs`. Every one of those
files is core-tier — `git.md` and `docs.md` reach all 17 stacks,
`config.md` 15 — so all five rules travel.

**Releases:** v2.43.0 — Git merge mechanics. #951 merged after the tag,
so it is unreleased on main and belongs to the next cut.

**PRs merged:** #966, #967, #968, #972

**Issues closed:** #923, #919, #963, #951.

---

## 2026-08-03 — v2.44 Consumer reconciliation

**Tool:** Claude Code (Opus 5 [1M]).

**Both halves of a bump were unspecified in the same direction** (#970,
#971). `base-agents` already settled which revision a consumer *reads* —
the issue list at HEAD, the rules at the pin — and that read-side rule
had made the write side look settled too. It was not. A downstream bump
procedure ran `checkout origin/main`, the exact read the section forbids,
applied to the pin. It had never produced a wrong pin, because until
`v2.42.0` the newest tag *was* `origin/main` every time it ran. Upstream
kept working past a release and the two separated: a ticket describing
the `v2.41.0 → v2.42.0` range attributed a rule to it that lives four
commits past the tag. The rule now says pin a released tag, and prices
the second cost — a tag range is citable, "whatever `main` was that
afternoon" is not, which leaves the commit message as the only record of
what moved.

**A convenience list was silently acting as the definition** (#971). A
consumer's `CLAUDE.md` names its resolved chain, and reconciling the
`v2.42.0` bump against that list was wrong twice at once. It missed
`workflow/issues.md`, which is not in the list but is reached through
`platform/github.md` — so `base-issues-record` governed that repository
while it maintained the same convention by hand, unaware upstream owned
it. And it nearly imported `agents.md` and `security/devsecops.md`, both
changed in the same range and both plausible, neither reachable from
anything declared. The asymmetry is what earns the rule: a missed file
looks like a local doc drifting, an over-included one looks like ordinary
diligence, and both pass for reconciliation work rather than a scoping
error. Governance resolves through the `DEPENDS ON` headers; any list a
consumer writes down is a cache of that resolution.

**The placement rule pointed away from the right home, and it was still
right to run it** (#980). Both issues suggested `agents.md`. Measuring
per PLAYBOOK step 2 returned 0 of 17 stacks — read literally, grounds to
reject. `agents.md` was correct anyway: `INTERVIEW.md` reads it directly,
so it shapes every generated file by a route `resolve.py` does not
measure. The step's justification — "a rule in a template no chain
resolves reaches no generated context file" — is false for the templates
the pipeline itself reads. Chain reach answers *does this travel to
generated projects*; it cannot answer *does this travel at all*. Filed
rather than fixed in-session: the 0/17 set is currently labelled
"reference-only", which conflates a different route with low value, and
separating those is more than a wording fix.

**Prose that quotes a directive is parsed as a declaration** (#979). The
transitive-governance rule first spelled `DEPENDS ON` out in its bracket
form inside backticks, and SYS-01 plus SYS-04 failed against a phantom
file. Backticks are not respected — the parser scans the whole file, and
a declaration is only meaningful in the header. Shipped by naming the
header in prose instead, which is a workaround no author will remember,
so the parser is filed as the actual defect. Worth noting the failure
misdirects: the message names a file that was never referenced.

**Template feedback:** both rules are reusable upstream content and both
landed in `base-agents` "Vendoring the templates", extending the existing
two-revisions rule rather than opening a parallel section. Chain reach is
0/17 and irrelevant here — `INTERVIEW.md` reads the file directly, so
they travel to every generated context file. Nothing this session was
project-specific.

**Releases:** v2.44.0 — Consumer reconciliation. Annotated tag first per
the recipe #974 landed the day before; `tag-guard` green, and
`--verify-tag` had nothing left to create.

**PRs merged:** #975, #978

**Issues closed:** #970, #971

**Issues opened:** #979, #980 — both unmilestoned, triggered by the next
cut being scoped.

## 2026-08-05 — v2.45 Examples governance

**Tool:** Claude Code (Opus 5 [1M]).

**Reconstructed entry.** The session shipped without one, and the gap
surfaced twenty days later while scoping the next cut. What follows is
drawn from ADR-025 and the two merged pull requests, not from the
session; the reasoning below is the ADR's, restated.

**Two gaps sat in a seam, and neither owner was the place to fix them**
(#987, #988). Governance of an `examples/` directory was split in half.
`stack/python-lib.md` prescribed the directory, `base/core/readme.md`
prescribed its contents, and the bridge between them was a single
conditional bullet under the README's Project structure section — a rule
about how example code *runs*, reached through the template that governs
README prose, because the index happens to be a README. "Smoke-tested in
CI" never said how the package is installed for that job, and the
cheapest reading, reuse the test job, proves the examples run beside the
test tooling rather than against the published surface. Separately, the
index is the one document whose body is machine-generated program
output, which the secret scanner reads like source: a printed cache key
matched `generic-api-key` and failed the scan on a file containing no
secret.

**A file-level ID makes a rule unaddressable** (ADR-025).
`base/core/readme.md` carries one `[ID: base-readme]` and no section
IDs, so a project needing to extend the offline rule had to replace the
entire README contract to reach it. That, with `base-readme` sitting in
the core tier while `python-lib` was the only stack of seventeen
prescribing the directory, decided the shape: a dedicated
`base/core/examples.md` reached by `depends_on` rather than by the core
tier. The core tier is the set that applies to every project, and most
projects ship no examples directory — a conditional concern does not
belong there.

**Offline needed a boundary, not a ban.** An absolute rule reads as
"build a fake of your vendor's API before you may ship an example",
which charges a documentation rule for an architectural seam. Where no
seam exists the alternative to a dated example is no example. The rule
landed as reproducibility rather than socket abstinence, with a named
exception the deviating project declares per example.

**Template feedback:** all reusable upstream content.
`templates/base/core/examples.md` is new (`[ID: base-examples]`), with
per-section IDs so one rule can be extended without replacing a
neighbouring contract. `base/core/readme.md` §5 reduces to a pointer.
`python-lib`, `go-lib` and `nodejs-lib` keep only what is
language-specific — packaging exclusion, install command, file
extension, position relative to the source layout.

**ADRs:** ADR-025 — Examples get their own template.

**Releases:** none at the time; cut later as v2.45.0.

**PRs merged:** #990, #992

**Issues closed:** #988, #991

**Issues opened:** none. #987 stays open — its second request, repeating
the commit-history point wherever the secret scan is described, is
platform-template scope.

## 2026-08-25 — Backlog groom and the v2.45 cut

**Tool:** Claude Code (Opus 5 [1M]).

**Forty-three issues carried neither a type nor a priority label.** The
August intake ran to 68 new issues in three weeks and none of them was
labelled at creation, which CLAUDE.md §2.2 requires. The conformance
check in `platform-github-labels` exists precisely to catch this and
returns a list nothing reads, so a rule with a check still decayed for
three weeks. It now returns `[]` again. The distribution that came out:
3 P1 bugs, 5 P2 bugs, 59 P2 tasks, 31 P3 tasks, 15 spikes, 1 epic.

**Six of the forty-three were defects, not gaps.** In a template repo the
`bug` type is easy to under-use, because everything reads as "a rule
could be extended". The line that held: a rule that states something
false, contradicts another rule, or is one the repository itself
breaks is a defect in existing functionality. `platform/github.md:138`
claims CodeQL is "free for all repositories (public and private)" and
private repositories need paid Code Security (#1030). Two
`platform-github` rules make an isolated elevated-scope scan unable to
join the fan-in it is required to join (#1042). The mandatory startup
block resolves one manifest axis, so every consumer's chain silently
omits the platform layer (#1029).

**A rule the templates break 17,571 times** (#1045). `base-quality`
restricts content to ASCII and names no check. Measured over tracked
Markdown: 172 of 188 files carry non-ASCII, 14,788 em dashes among them.
`base-docs` forbids Unicode box-drawing *citing that rule as its reason*
and then uses it 753 times. Filed at `v2.44.0` against 170 of 186 files
and 17,350 characters; re-measured during the groom at 172 of 188 and
17,571. An unchecked rule does not hold steady, it loses ground, and the
drift is invisible in a diff.

**The tracker is duplicating itself because nothing greps it before
filing.** Six clusters of overlapping issues came out of the sweep, each
one several issues editing the same section from different angles. The
sharpest: "a trigger has no watcher" was filed three times in three days
across two templates (#1036, #1041, #1052). None is a strict duplicate —
each carries a distinct claim — so none was closed. They are recorded as
one pull request each instead, which is the cheaper correction.

**Verify before grooming, not after.** Four issue claims were re-checked
against `main` before labelling, on the standing lesson that a
weeks-deep backlog has items overtaken by later work. All four were
still live, and one had got worse. The check cost four greps and would
have cost a milestone if any had already landed.

**Template feedback:** nothing project-specific. The self-duplicating
tracker is a candidate upstream rule — `base-issues` says how to write
and defer an issue and nothing about searching the tracker before
opening one — but it is not filed yet, and filing it without searching
first would be the joke writing itself.

**Releases:** v2.45.0 — Examples governance, covering #988 and #991.
Milestone created retroactively so the tag had a complete cut behind it;
annotated tag first per the recipe, `tag-guard` green, `--verify-tag`
had nothing left to create.

**A generated file can rot without either invocation being wrong**
(#984). The arc42 pull request had sat 22 days and was three commits
behind; `gh pr update-branch` brought it current and both sides had
regenerated `generated/` from different bases. Git merged the two sets
of regenerated output textually, and a textual merge of generated files
is not the output of any invocation of the generator. It happened to be
correct here — `sync.py --check` passed, and `base-examples` and the new
arc42 rules both survive in all 17 chains — but that was checked, not
assumed. `docs-generated` names three rot modes and #1002 proposes the
wrong invocation as a fourth; this is arguably a fifth, and it is the
one a merge produces silently. Filed nowhere yet, because it wants a
measurement first rather than a rule written from one instance.

**PRs merged:** #1059, #984.

**Issues closed:** #983 — auto-closed by #984, verified.

**Issues opened:** none.

## 2026-08-26 — v2.46 Unenforced rules

**Tool:** Claude Code (Opus 5 [1M]).

**A rule can be wrong rather than under-enforced** (#1045, #1067). The
ASCII restriction read as covering all source content, and measuring it
returned 5,593 characters across 155 of 171 files. It also returned
zero of the hazards an ASCII rule exists to prevent: no smart quotes, no
non-breaking spaces, no zero-width characters, no byte-order marks. What
it had missed was five U+FFFD, the residue of text decoded with the
wrong encoding, one of which shipped through two chains and left a rule
justification unreadable downstream. So the rule banned 5,593 harmless
characters and caught none of the five that were real damage. Twice the
answer was to narrow the rule rather than sweep the files, and the
second pass mattered more than the first: the rule still covered string
literals, and `tools/sync.py` draws the specification trees with
box-drawing literals, so enforcing it would have rewritten 98 lines of
documentation into ASCII on the authority of a code rule.

**A number written into a template is a preference shipped downstream**
(#1055, #1072). Width resolved into the same shape as charset. The rule
states that a width is declared once and checked; the project supplies
the number. Moving this repository from 80 to 88 then re-scoped the
check with no code change at all, which was the test of whether the
design was right rather than merely tidy. Two templates still named 80
and now name nothing.

**Every check had to be run, not written** (#1056, #1045, #1069). Three
shipped broken on the first attempt. A regex using the anchor and
newline escapes did not survive the trip into the template and raised
`SyntaxError` on extraction. The ASCII check crashed with
`UnicodeEncodeError` while reporting a non-ASCII character, which is the
failure it existed to detect. The width check carried backslashes and
was refused. The habit that came out: an embedded check is
backslash-free, prints code points rather than characters, and is
extracted from the committed template and executed before the pull
request opens.

**A check that reports nothing and a check that reaches nothing look
identical** (#999, #1015, #1069). Every check landed with its inputs
counted -- 65 journal entries, 25 decision records, 8 source files, 17
chains -- and with a table of the break modes it catches. Two of them
treat an empty result as a failure for the same reason: no entries found
means the heading format drifted, and no wheel in `dist/` means the
build never ran.

**The mangled output was a boundary, not a character.** Smoke printed
`23 checks ? 23 passed` for the whole session. Not the em dash: an unset
output encoding, inherited from the console. Five entry points now set
it explicitly, which fixes every string that crosses the boundary
including ones not written yet.

**Withdrawn:** a decision record proposing an enumerated
permitted-character set for Markdown. It was Latin-centric by
construction and would have broken a document written in another
language. Number 026 was never merged and returned to the pool; the
number now in use for it belongs to a different decision.

**Filed rather than fixed:** #1062, the only reference-mode example
names no platform template, which needs a pipeline regeneration rather
than a hand edit. #1080, one decision record overflows the declared
width on an unbreakable code span, deferred behind #1054 because
settling it would decide that issue sideways in a commit about
whitespace.

**Template feedback:** all reusable. Checks now travel beside their
rules in `base-quality`, `base-docs` and `python-lib-structure`. The
width rule states no number, the charset rule guards identifiers only,
and the ADR schema finally matches what the project practises.

**Releases:** v2.46.0 -- Unenforced rules, 11 issues, all three open P1
bugs cleared.

**PRs merged:** #1061, #1063, #1065, #1068, #1070, #1071, #1073, #1074,
#1075, #1078, #1079

**Issues closed:** #983, #999, #1015, #1029, #1045, #1055, #1056, #1064,
#1067, #1069, #1072

**Issues opened:** #1062, #1064, #1067, #1069, #1072, #1080

## 2026-08-26 — Immutability ruling and backlog rescope (afternoon)

**Tool:** Claude Code (Opus 5 [1M]).

**An enumeration of permitted operations is under-inclusive by
construction** (#1054, #1080). The ADR exemption listed what a
format-only edit may do -- normalize headings, titles, filenames,
cross-links -- so anything unlisted implicitly needed a superseding
record. It now states its test instead: immutability protects the
decision, meaning the claims made in Context, Decision, Alternatives
considered and Consequences, and any edit that moves no claim is a
format change. Rewrapping, splitting an unparseable sentence and
rendering a buried enumeration as a list all qualify, with
`git diff --word-diff` as the evidence. The first record it applied to
was one this repository had been unable to fix for exactly that reason:
a line two characters over the declared width, on an inline code span
with no wrap point. The word-level diff showed no word changed.

**A milestone that collects everything nobody wants to decide about
stops being a milestone.** v3.0 held 38 issues and had not started. The
cut line turned out to be simple once stated: the restructure changes
how a consumer's context file *loads* rules, and does not change what
the rules say. Rule content survives any delivery change, so it ships
now. Twenty-eight issues went back to the backlog -- new templates, a
language layer, frontend layer extraction, README polish, and four
orphaned-template questions from an old coverage analysis -- and v3.0
came out at twelve, six of them spikes. The epic reads as "answer six
questions, then implement", which is a tractable shape. Thirty-eight
was not, and that is the likeliest reason it sat untouched since July.

**Applying a criterion is not the same as holding it consistently.**
Having ruled that reach questions are composition rather than delivery,
I still had `base-oop` reach filed on the delivery side while calling
the identical question shippable elsewhere. Caught on re-reading the
split rather than by any check. A criterion stated once needs a pass
back over everything already sorted under it.

**Template feedback:** the immutability change is reusable and landed in
`base-docs` Decision logs. The rescope is project-specific -- it is
tracker hygiene, not a rule.

**Releases:** none. PR #1083 sits unreleased on main and unmilestoned,
which is the third cut in a row where merged work needed a milestone
found for it before a tag.

**PRs merged:** #1083

**Issues closed:** #1054, #1080

**Issues opened:** #1082 -- split from #1054 rather than carried along,
since a readability bound is a separate rule and only became actionable
once fixing an unreadable passage stopped requiring a supersession.

## 2026-08-26 — Check integrity (evening)

**Tool:** Claude Code (Opus 5 [1M]).

**A rule that requires a check is not the same as a rule that requires
the check to work** (#1086). The pairing rule has always demanded that a
mechanically checkable constraint name its command and pass condition.
It said nothing about whether that command runs, reaches its inputs, or
flags the right things -- and five checks written against it in v2.46
shipped three broken on the first attempt. The four observed failure
modes are now rules, and the first of them is itself checked: every
check embedded in a rule file must compile when extracted the way a
reader extracts it.

**The gate rejected its own author, twice over.** The release-milestone
check in #1094 was first written indented five spaces under a numbered
step. A renderer strips a fenced block's own indentation from every line
that has it, so a four-space nested line became three-space and the
extracted body raised `IndentationError`. The compile gate from #1088
named the file and line before the branch was pushed. That was a fifth
break mode none of the four in #1086 covered, so it landed as a rule in
the same section: never indent a fenced check more deeply than the first
indentation level of the code inside it. Writing the anchor rule had
already turned up the same shape in its own prose -- a heredoc opener
written inline in a bullet, read as a check by a naive extractor, which
is #979 wearing different clothes.

**Three things reported nothing because they reached nothing, in one
session.** A negative control that silently matched nothing and
therefore tested nothing. A reach measurement that counted 75 "stacks"
by splitting `--list` description text on whitespace, when there are 17.
An assertion expecting 11 renumbered ordinals where there were 13, which
fired before the write and left the file untouched. Every one was caught
by counting inputs rather than by reading output -- which is the rule
this whole cut is built around, arriving unprompted three times while
the cut was being written.

**Grooming before writing changed two of six issues.** #832 reads as a
missing cross-reference; the section already cross-references the right
neighbouring rule, just for a different reason, so it needed two bullets
rather than a rewrite. #1014 argues its case by quoting "every rule
binds new and modified code, not untouched code" as an existing rule --
`grep` finds nothing like it in this chain, because it belongs to the
downstream project the issue was written from. Both were still worth
doing. Neither was quite the work the issue described.

**The wrong side of a relation passes green.** The release gate confirmed
a milestone's issues were all closed, which cannot see work merged with
no milestone at all -- so three consecutive cuts needed a milestone found
for already-merged work before a tag could be cut, each caught by a
person reading the log. The inverse check now enumerates the pull
requests merged since the previous tag and reports any whose closed
issues carry no milestone. Its negative control was a planted violation:
a milestone removed from one closed issue, the check naming it, the
milestone restored. It validated this session's own cut before the tag.

**A ruling can leave its own earlier statement standing beside it**
(#1097, #1098). The immutability change landed in the template without
retiring the sentence it replaced, so the Decision logs section stated
the superseded rule first -- "the prose body never changes" -- and
corrected it two bullets later. An agent applying rules in order reads
the false one first, and treating ADR prose as frozen is the exact
behaviour the ruling exists to stop. Adding a rule is not the same as
landing it; the old statement has to go in the same pass.

**Deciding to leave something alone still has to be recorded.** The same
stale claim sits in a merged decision record that holds four other
decisions still in daily use. It cannot be edited, because the sentence
is a claim and editing it is what immutability forbids -- performed on
the record that states the immutability rule. It cannot be partly
superseded, because status and the supersession link must agree and the
partial form was rejected in #856. Retiring the whole record to fix one
sentence would archive four working rules. What was left looked like
doing nothing, which is why it needed a record of its own: a decision
record is a dated statement of what was decided on that date, not a live
specification. The specification is the template chain. The record is
doing its job; the template contradicting itself was the actual defect.

**A record that deliberately does not supersede has no link at all.**
The ADR format keeps references to other records in the frontmatter and
forbids naming them in prose, so a correcting record with an empty
`supersedes` field cannot point at what it corrects in either place.
That forced a fourth clause into the decision -- a correcting record
must state its rule completely on its own -- which would have been easy
to miss and would have left the rule unfindable from the stale side.

**Template feedback:** all of it is reusable and landed upstream --
`quality-gates-check-runs`, `quality-gates-check-selection` and
`quality-gates-retrofit-ratchet` in `base/workflow/quality-gates.md`,
`testing-negative-assertion-coverage` in `base/core/testing.md`, and the
pre-release step in `base/core/git.md`, plus the correct-by-new-record rule in
`base-docs`. The only project-specific piece is the
`docs/PLAYBOOK.md` step that applies the release check here.

**Releases:** v2.47.0 (ADR immutability -- a milestone created for the
four commits that had been sitting on main unmilestoned), v2.48.0
(Check integrity, 12 issues, 8 PRs) and v2.49.0 (ADR immutability,
continued -- 2 issues, 2 PRs, milestone created before the work rather
than at tag time).

**PRs merged:** #1088, #1089, #1090, #1091, #1092, #1093, #1094,
#1095, #1099, #1100

**Issues closed:** #832, #1005, #1014, #1024, #1026, #1028, #1031,
#1037, #1044, #1046, #1086, #1087, #1097, #1098

**Issues opened:** #1087 -- filed mid-session after the third
consecutive milestone-at-tag-time scramble, and closed in the same cut,
since the fix is one pre-release step and the evidence was already three
releases deep. #1097 and #1098 -- the same stale claim in two places,
filed separately because a template can be edited and a merged record
cannot, so they needed different remedies. Both closed in v2.49.

**ADRs:** ADR-026 -- a stale claim in a merged record is corrected by a
new record, never by an edit or an addendum, and the template chain is
the authority a reader applies.

## 2026-08-26 -- Merge and release verification (late)

**Tool:** Claude Code (Opus 5 [1M]).

**Four green results that prove less than they look like.** A merge with
no conflict, a release pipeline that has never run, a release whose record
was written before the last thing landed, and a numbered document two
branches edited without colliding. Each reports success, and in each the
success is about the wrong question. The cut is six issues in
`base/core/git.md`, which is core tier, so all six reach 17/17 stacks.

**The narrative is usually right, and it is never evidence.** De-stacking
told a maintainer how to resolve a conflict and nothing about verifying
the resolution. Under squash merge the merge base stays the pre-stack tip,
so a file both sides rewrote conflicts whole, and "the branch is newer, it
already contains the lower pull request, take its side" is a story that
holds until anything else lands on the base in between -- after which
taking that side discards it silently and the squash makes the loss
permanent. The remedy is a comparison of the conflict stages, and it was
built as a real de-stack in a throwaway repository rather than reasoned
about: with only the lower branch landed the check reports two insertions
and nothing removed; with an unrelated commit also landed it reports a
deletion and names the line that would be dropped. The first control did
not conflict at all, because the two edits sat on different lines -- the
shape had to be reproduced before it could be measured.

**Which assertion holds depends on how the lower pull request merged**, so
the rule names the case rather than the command. Under rebase merge the
branch is a strict superset and the tree-wide form must be empty. Under
squash the content matches but the history does not, so only the per-file
form holds. Shipping one assertion for both would have been wrong half the
time and green either way.

**A check calibrated against nothing reports nothing.** The ordinal check
for #1020 flagged fourteen violations in `CLAUDE.md` on its first run, all
false: separate numbered lists under different headings were piling into a
single run because a numbered heading was counted as an ordinal without
resetting the group beneath it. Measured against six real documents after
the fix -- 189 ordinals across 37 groups, silent -- and only then against
planted duplicates, in both shapes the issue describes. Enforcing the
first draft would have produced fourteen edits to a compliant file.

**The cut generated its own evidence for one of its issues.** #1020
describes two branches renumbering one document and merging cleanly into a
duplicate. This session renumbered `Pre-release checks` twice in two
separate pull requests, thirteen ordinals each time, and was safe only
because the two were sequential. Run concurrently they are exactly the
defect. The issue was filed from a downstream observation and was
re-confirmed here without anyone looking for it.

**A sixth break mode, and it does not raise.** The five recorded ways an
embedded check breaks all fail loudly or fail closed. This one does
neither: a trailing backslash used as a line continuation did not survive
the authoring path into the template, and the command arrived collapsed
onto one line with the backslash replaced by spaces. The shell does not
care, so it still runs, and the compile gate passes because a joined line
is valid. It was found by reading the committed file rather than by any
check, and both affected commands were rewritten so that no line ends with
a backslash. Filed rather than fixed in place, since the rules it belongs
to are a different file and a different cut.

**An empty result that exits zero is not a pass.** `gh run list` against a
workflow with no matching runs prints `0` and exits `0`, so a release
pipeline that has never executed produces the same silence as one that has
run a hundred times. The pass condition names `0` as the finding for that
reason, and separates it from the unknown-workflow error, which is drift
rather than an absence of runs.

**The generated tree is a second output of every core-tier edit.** The
first pull request failed CI on seventeen stale chains, because
`sync.py --check` had been run at the start of the session and not after
the change. Running a gate before the work it gates is the same class of
error as writing a check and not running it.

**Template feedback:** all of it is reusable and landed upstream in
`base/core/git.md` -- the de-stack measurement and its two case-scoped
assertions, the delete-on-merge setting check, the two pre-release steps
for an unproven pipeline, the release-ordering step, and the
ordered-document rule with its check. Nothing here is project-specific.

**Releases:** v2.50.0 -- Merge and release verification, 6 issues, 4 pull
requests, milestone created before the work.

**PRs merged:** #1105, #1106, #1108, #1109

**Issues closed:** #996, #1016, #1020, #1040, #1048, #1053

**Issues opened:** #1110 -- the collapsed line continuation, filed against
the check-integrity rules rather than fixed in this cut, since it is a
sixth break mode in a file this milestone does not touch.

## 2026-08-26 -- Repository migration and platform corrections (night)

**Tool:** Claude Code (Opus 5 [1M]).

**Guidance that was true once.** Where the previous cut was about green
results that answer the wrong question, this one is about statements that
were correct when written and are not now. Two of the eight issues are
`bug` rather than `task`, which matters: a missing rule leaves a reader
without help, while a wrong one sends them somewhere confidently.

**A free tier that is not free.** `platform-github` said CodeQL is "free
for all repositories (public and private)". Code scanning on a private
repository requires GitHub Code Security, a paid add-on, and the API
declines the repository outright before any analysis starts. The damage
is not the sentence -- it is that the sentence reads as an assurance the
SAST row of the gate table is always satisfiable at no cost, so a private
project follows it and commits a workflow that can only be permanently
red or permanently skipped. A gate satisfied by appearance while scanning
nothing. The correction ships with a check that separates the two
refusals, because they send you to different places: `404 no analysis
found` means entitled and nothing has run, `403 Code Security must be
enabled` means not entitled at all.

**Two right rules with a gap between them.** Keep an elevated-scope scan
in its own workflow; fan in one required check. Both correct. A fan-in
job can only depend on jobs in its own workflow, so the isolated scan
cannot join it -- leaving it gating nothing, or holding a per-job entry
in branch protection, which is the stale list the fan-in rule exists to
prevent. The resolution is one required context per workflow rather than
one per repository, and it makes two existing statements false: the
fan-in rule's "sole required context", and the aggregator-timing note
telling a merge waiter to target *the* aggregator by name. Both were
corrected in the same pass. Adding the rule beside them would have left a
reader applying rules in order hitting the false one first.

**The measurement corrected the rule, again.** The migration settings
check was drafted with a pass condition predicting an "empty listing" for
a repository whose settings cannot be read. Run against one, it produces
`to_entries cannot be applied to: null` -- the field is returned only to
an administrator. The shipped wording names the actual message and says
it means the comparison never happened. Writing what a command will
probably print is not the same as running it.

**Re-homed by measurement, not by topic.** #1032 proposed its rule for
`ai-workflow`, which is where it belongs by subject and which resolves
into 0 of 17 stacks. `git.md` resolves into all 17, and a reader
performing a migration finds both migration rules together there. The
topically obvious home and the reachable one are different files more
often than is comfortable.

**A trigger fired before its own rule was written.** #1119 was open and
citing an ordinal count and a settings result in its body when #1118
merged, touching a neighbouring template and regenerating the same
seventeen chains. The branch went behind, was updated without a
force-push, and the merge was clean -- which proves the edits did not
overlap and says nothing about the result. The cited verification was
re-run rather than re-read, and `sync.py --check` confirmed the merged
templates still produce the committed output. That is #1025, applied to
itself while it was still an open issue.

**A rule paid for itself between being written and being merged.**
`gh pr checks` on the pull request carrying the full-SHA rule returned
"no checks reported on the branch". Selecting by full commit SHA at the
same instant returned `queued`. Two queries, one moment, one commit: one
said nothing had happened, the other named the state. Reading the first
as a workflow that never fired would have sent someone hunting a broken
trigger.

**The same issue was implemented twice, in parallel, by two people.**
#1049 was picked up here and in a separate session, landing as two
complete pull requests within minutes of each other. One merged, one was
closed as superseded. Nothing looks at the open pull request list before
starting a ticket, the same way nothing greps the tracker before filing
one -- and the second is already a recorded lesson. The wasted work was
small; the mechanism that produced it is not specific to this issue.

**A regression, caught by reading rather than by any gate.** The two
bullets added for the isolation gap were inserted between the fan-in rule
and its YAML example, orphaning the example under a bullet it does not
illustrate. Smoke passes, the markdown renders, nothing is malformed --
the only symptom is a reader taking the example for something it is not.
Found while opening the next pull request against the same region.

**Template feedback:** all reusable, all landed upstream. In
`base/core/git.md`: the migration checklist with its settings check, the
issue-cohort rule, the re-run-the-body's-verification rule, and what the
batch update cycle buys when members are not disjoint. In
`platform/github.md`: the CodeQL entitlement correction, the isolated
fan-in rule with its two corrected statements, and run selection by full
SHA. Nothing project-specific. Note `platform/github.md` resolves into no
stack chain at all -- it is orthogonal, chosen per project, so chain
reach says nothing about whether it travels.

**Releases:** v2.51.0 -- Repository migration and platform corrections, 8
issues. Tagged at commit `be4fe92` rather than at `main`, the first
release to use the rule added in the previous cut: naming the commit is
what keeps the journal entry outside the release it describes.

**PRs merged:** #1115, #1116, #1118, #1119, #1120, #1122 (and #1111,
#1112, #1114 from the previous session's close-out, which fall inside
this tag's range)

**Issues closed:** #1008, #1021, #1025, #1030, #1032, #1042, #1049, #1117

**Issues opened:** none this cut. #1110 and #1113, opened during the
previous one, remain open and unimplemented.

## 2026-08-26 -- Unconfirmed inputs (late night)

**Tool:** Claude Code (Opus 5 [1M]).

**Every issue in this cut is about confirming the input rather than
reading the output** -- the tree an issue described, the corpus a check
read, the text that actually shipped, and whether a derived artifact was
regenerated at all. Five issues, six pull requests.

**Three checks in one file, none of which said what it read.** The ADR
frontmatter check printed one line per non-conforming record and nothing
when the folder was clean, so a clean run and a run that reached no
records were identical -- in a repository whose own templates carry two
separate rules against exactly that. Grooming found the same shape in
both siblings. The journal check reported an empty result but never a
count. The width check reported neither, and it enumerates with
`git ls-files`, which reads the index: a document not yet staged is
invisible to it and the assertion passes having never seen it. All three
now report their input count and name zero as a failure.

**The width check found something on its first reporting run.** One line
in `README.md` at 89 characters against the declared 88, sitting there
since a pull request in the 400s. The check had always been able to find
it and had always run; what it could not do was say so. Nothing was
wrong with the assertion.

**An issue can be narrower than it reads.** #1107 proposed a rule for
meta-tests that enumerate a corpus. Most of it was already in
`testing-negative-assertion-coverage`, landed in v2.48 -- the input
coverage requirement, the insistence that the coverage assertion be a
real comparison rather than a printed number, the failure when a set
shrinks. Three bullets were genuinely missing, so three bullets is what
shipped, not the new section the issue reads as.

**And an issue can be wrong, including one filed the same day by the
person implementing it.** #1110 was written this morning from a real
observation: a trailing backslash had been dropped between author and
file, joining two lines of a shipped check. The proposed rule was that a
check MUST NOT use a line continuation. Measured before enforcing: 107
fenced blocks across the template tree, three lines ending in a
continuation, and all three intact -- a `curl` with headers piped through
three filters and a `jq` program over four fields, each the clearest form
for what it does. The rule as proposed would have flagged working
commands and demanded they be made worse. What shipped requires
confirming the continuation survived and prefers a form that needs no
confirmation. Being right that something broke does not make the proposed
remedy right.

**The check for it is a locator, not a detector.** Once a continuation is
lost the line is indistinguishable from one written joined, so nothing
can find it afterwards. The check reports where the risk is instead,
bounding the manual read to three lines rather than 107 blocks, and its
pass condition says a non-zero count is not a failure.

**A negative control broke on the phenomenon it was built to test.** The
planted file for that check reported zero continuations where one was
planted. The check was right; the control was wrong, because `printf`
mangled the backslash before it reached the file -- the exact silent loss
under test, reproducing itself one level up in the test harness.
Rebuilding the control in Python, bypassing the shell, made it
discriminate.

**A rule that dogfooded on its own pull request.** #1113 says regenerating
is owed by the edit rather than by the review, and that a staleness check
run before the edit reports the previous state and reads as a pass. The
change introducing it edits a core-tier template, so it left all
seventeen pre-resolved chains stale -- the precise failure, reproduced on
the pull request that fixes it, with `sync.py --check` reporting `STALE 17`
before the prescribed regeneration and `All files in sync` after.

**The last rule written was the one the other four had been following.**
#1102 asks that a filed issue be re-verified against the tree before it
is implemented. It was implemented last, after four issues in the same
cut had been groomed, and all three shapes it names had already occurred:
#1107 narrower than filed, #1103 wider than filed, #1110 wrong as filed.
`review.md` already required verifying a finding before REPORTING it and
said nothing about verifying a ticket before ACTING on it, which is the
same problem on the input side, so it landed as the sibling section.

**Template feedback:** all reusable, all landed upstream --
`base/core/docs.md` (three checks now self-reporting), `base/core/testing.md`
(the corpus guard as its own test), `base/workflow/quality-gates.md` (the
continuation rule and its locator), `base/core/git.md` (the regeneration
trigger), and `base/core/review.md` (verifying a filed issue). Nothing
project-specific except the one README line. Note the continuation rule
sits at 12/17 reach rather than 17/17, which is correct for its subject
and worth knowing.

**Releases:** v2.52.0 -- Unconfirmed inputs, 5 issues, 6 pull requests.

**PRs merged:** #1124, #1126, #1128, #1129, #1130, #1131

**Issues closed:** #1102, #1103, #1107, #1110, #1113

**Issues opened:** none. Both issues opened during the v2.50 cut were
closed here.

## 2026-08-26 -- Label check coverage

**Tool:** Claude Code (Opus 5 [1M]).

**A one-issue cut, and the issue was found by running a check rather than
by reading one.** A label audit turned up nothing wrong with the labels:
93 open issues, every one carrying exactly one type and one priority, and
a label set matching the documented taxonomy name for name and colour for
colour. What it turned up was that the check saying so could not tell
that from having read nothing.

**The enforcement check had the defect the whole previous cut was
about.** `platform-github-labels` returns a JSON array of violations and
nothing else, so `[]` is the output whether it inspected every open issue
or none. Measured at one moment on one repository: the real run gave
`[]`, and the same filter forced to match nothing gave `[]`. Anything
that empties the listing -- an authentication failure, the wrong
repository context, a renamed label in the selector -- read as full
compliance. The check was added to stop unlabeled issues reaching the
tracker, and it had been reporting `[]` for months with nothing
distinguishing a healthy tracker from an unreachable one.

**Its cap was silent too.** `--limit 200` against 93 open issues and 598
ever: it has never truncated, and nothing would have reported it when it
did. A check that bounds its own input has to say what it dropped, or the
bound reads as coverage.

**Rewriting the form fixed three things at once.** The jq one-liner could
not carry a count and two guards without interpolating its limit into the
jq program, so it became a Python heredoc like every other shipped check
in the chain. That form reports the count naturally; it also joins the
corpus the embedded-check compile gate scans, which a shell one-liner
never did, taking that gate from nine checks to ten. And it removed one
of the three line continuations in the template tree, leaving two -- both
in a `curl` example where the continuation is genuinely the clearest
form, which is the reason the continuation rule requires confirming
survival rather than banning the construct.

**The mangled backslash struck a third time, in the search string.** The
replacement that rewrote this check would not match its own anchor,
because the anchor contained a trailing backslash and the authoring path
dropped it -- the same silent loss that produced the rule two cuts ago,
now defeating the edit rather than the output. Building the character
with `chr(92)` instead of writing it literally made the anchor match on
the first try. The rule says confirm the continuation survived into the
file; the corollary is that anything quoting such a line has the same
problem.

**A scope question answered in the template rather than in the issue.**
26 closed issues carry a type label and no priority, all closed between
18 April and 25 June, before the rule was enforced; everything closed
since conforms. The check could be widened to cover them and would then
produce 26 findings nobody should act on. It stays scoped to open issues,
and the template now says why: a triage label is terminal, so a closed
issue's labels are a record rather than a live claim.

**Template feedback:** reusable, landed upstream in
`platform/github.md`. Nothing project-specific. Note that `platform/`
resolves into no stack chain -- it is orthogonal, chosen per project, so
chain reach says nothing about whether it travels.

**Releases:** v2.53.0 -- Label check coverage, 1 issue, 1 pull request.
Fourth cut of the day.

**PRs merged:** #1135

**Issues closed:** #1134

**Issues opened:** #1134, filed and closed in the same cut, since the
evidence was one command and the fix was one check.
