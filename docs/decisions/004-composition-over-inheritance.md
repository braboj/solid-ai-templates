---
id: "004"
status: Accepted
date: 2026-05-04
category: composition
supersedes: []
superseded_by: []
---

# ADR-004: Composition over inheritance in dependency model

## Context

ADR-001 established a three-layer inheritance model: `base/ -> layer/ ->
stack/`. This works well for the main chain, but `quality-gates.md`
introduced a transitive dependency problem.

`quality-gates.md` declares:
```
[DEPENDS ON: base/quality.md, base/git.md, base/testing.md, base/devsecops.md, base/cicd.md]
```

It depends on `devsecops` and `cicd` because they are conceptually related
to quality enforcement. However, `quality-gates.md` is entirely
self-contained — it defines the three-layer gate model, categories table,
thresholds, and tool constraints without referencing any content from
`devsecops.md` or `cicd.md`.

This creates two problems:

1. **Interface Segregation violation.** Any template that resolves
   `quality-gates` transitively inherits `devsecops` (SAST, SCA, SBOM,
   DAST) and `cicd` (pipeline stages, environments, deployment). A static
   site on GitHub Pages gets SBOM requirements and multi-environment
   deployment rules it will never use.

2. **Transitive surprise via platform templates.** `platform-github`
   depends on `quality-gates`, so every project using GitHub as its
   platform inherits `devsecops` + `cicd` — regardless of whether the
   project needs them.

Additional finding: `static-site-astro.md` lists `base/quality-gates.md`
in its file header `[DEPENDS ON]` but the manifest does not include it.
This is a hand-curation drift that demonstrates the fragility of
the current model.

### SOLID analysis of the violation

| Principle | Violation |
|-----------|-----------|
| **S — SRP** | `quality-gates` forces loading of unrelated modules via `depends_on` in addition to defining the gate model |
| **O — Open/Closed** | Adding a new infrastructure tier requires modifying `quality-gates`' dependency list |
| **I — ISP** | Consumers depend on fat transitive chains they only partially use |
| **D — DIP** | `quality-gates` depends on concrete templates (`devsecops`, `cicd`) instead of being a self-contained abstraction |

## Decision

Adopt composition over inheritance for the dependency model. Stacks
compose only the modules they need — no transitive surprises.

### Changes

1. **`quality-gates.md`**: remove `base-devsecops` and `base-cicd` from
   `depends_on`. The file is self-contained; it references the *concepts*
   of CI and security scanning (in the categories table) but does not
   require the agent to have read those files. It acts as a **facade**
   over the gate model.

   Before:
   `[DEPENDS ON: base-quality, base-git, base-testing, base-devsecops, base-cicd]`

   After:
   `[DEPENDS ON: base-quality, base-git, base-testing]`

2. **Core tier** (implicit, always loaded by convention): `quality`,
   `git`, `docs`, `readme`, `testing` — these 5 files apply to every
   possible stack. They are not declared in `depends_on`; agents load
   them as part of the startup protocol.

   Files excluded from core despite being common:
   - `review` — solo projects may not have peer review
   - `scope` — only relevant for agent-assisted development
   - `issues` — only relevant when using an issue tracker
   - `quality-gates` — depends on tooling choices, not universal

   These remain opt-in: projects that use them declare them explicitly
   or include them in the startup block.

3. **Opt-in tiers** (stacks declare what they need):

   | Tier | Modules |
   |------|---------|
   | Language | typescript |
   | CI | cicd, quality-gates |
   | Security (app) | security |
   | Security (pipeline) | devsecops |
   | Infrastructure | containers, deployment, release |
   | Session | scope, issues, review |
   | Specialized | data-quality, 360, ai-workflow |
   | Platform | github, gitlab |
   | Frontend | ux, quality, static-site |

4. **Stacks that need devsecops/cicd** declare them explicitly. Currently
   only `stack-terraform` declares both. Production backend stacks should
   add them if they need pipeline security scanning.

5. **Fix stale file headers**: align `[DEPENDS ON]` in file headers with
   `manifest.yaml`. The manifest is the source of truth.

### What this does NOT change

- The three-layer model (`base/ -> layer/ -> stack/`) remains intact
- `[EXTEND]` and `[OVERRIDE]` directives work the same way
- `manifest.yaml` remains the single source of truth for dependencies
- ADR-001 is not superseded — this decision refines it

### Design patterns applied

| Pattern | Application |
|---------|-------------|
| **Facade** | `quality-gates` defines the gate model without dragging implementation details — it references CI and security concepts without depending on the full templates |
| **Composition** | Stacks compose tiers explicitly instead of inheriting transitive deps |
| **Interface Segregation** | Fat modules split into focused, independently consumable units |

## Alternatives considered

1. **Profiles (minimal/standard/full)** — preset compositions per project
   complexity. Rejected: adds indirection without solving the root cause.
   Explicit composition is simpler and fully auditable. A profile is just
   a named shortcut for a `depends_on` list — the agent resolves the same
   files either way.

2. **Keep inheritance, trim quality-gates only** — remove devsecops/cicd
   from quality-gates but keep the inheritance model everywhere else.
   Rejected as too narrow: the same pattern will recur as new modules
   are added. Establishing composition as the principle prevents future
   violations.

3. **Remove quality-gates entirely** — inline the gate model into each
   stack template. Rejected: duplicates the three-layer model across 30+
   stacks. The facade role of quality-gates is valuable.

## Consequences

- Platform templates (`github`, `gitlab`) no longer transitively pull in
  `devsecops` and `cicd` — projects that need them declare them
- `quality-gates.md` becomes a lightweight facade (~140 lines) with only
  3 dependencies instead of 5
- File headers and manifest must stay in sync — stale headers are bugs
  (reinforces the case for #150: agent-side resolution from manifest)
- Existing stacks need a one-time audit to add explicit `devsecops`/`cicd`
  if they genuinely need them
- No breaking change for downstream consumers — removing transitive deps
  only removes rules that were noise for those projects

## Stack classification: cicd and devsecops

`quality-gates` defines *what* to check (SAST, secret detection).
`devsecops` defines *how rigorously* (SBOM per release, DAST on staging,
pen testing, license audits). `cicd` defines pipeline architecture
(staging/prod environments, artifact promotion, zero-downtime deployment).

Simple projects need the what (quality-gates). Deployed services need
both the what and the how (quality-gates + devsecops + cicd).

| Category | Stacks | cicd | devsecops | Reasoning |
|----------|--------|------|-----------|-----------|
| Static sites | astro, hugo, tutorial | No | No | Build-and-upload pipeline. Quality-gates + platform template covers SAST/secrets. No staging, no SBOM, no DAST. |
| Libraries | python-lib, go-lib, nodejs-lib, rust-lib, c-embedded | No | No | Publish is a release step. Platform template covers scanning. |
| Backend services | flask, fastapi, django, express, nestjs, spring-boot, go-echo | Yes | Yes | Real pipelines with staging/prod. Runtime attack surface needs full security policy. |
| Full-stack | nextjs, sveltekit | Yes | Yes | Same as backends — server-side code with deployment pipeline. |
| Workers / gRPC | celery-worker, go-grpc, python-grpc, java-grpc | Yes | Yes | Deployed services with runtime attack surface. |
| Mobile | react-native, flutter | No | No | App store builds, not traditional CI/CD. No DAST/SBOM. |
| IaC | terraform | Yes | Yes | Already declares both. |

### Platform templates as facades

`platform-github` mentions CodeQL, gitleaks, and Dependabot — all
devsecops concepts — but does NOT depend on `devsecops.md`. It is a
tool mapping layer: it answers "which tool for which quality-gates
category on GitHub?" Projects that need the full devsecops policy
(SBOM, DAST, license compliance, false positive documentation) declare
`devsecops` explicitly. This keeps the composition clean:

```
Static site:   platform-github                    (tool mappings only)
Backend:       platform-github + devsecops        (tool mappings + full policy)
```

The same facade principle applies to `platform-gitlab`.

### File header policy

File `[DEPENDS ON: ...]` headers MUST list direct dependencies only —
matching the manifest's `depends_on` for that stack. Headers MUST NOT
expand transitive dependencies.

Audit found 3 stale headers where transitive deps were expanded:

| Stack | Header deps | Manifest deps | Action |
|-------|-------------|---------------|--------|
| static-site-astro | 8 (expanded + quality-gates) | 2 | Align to manifest |
| static-site-hugo | 6 (expanded) | 1 | Align to manifest |
| static-site-tutorial | 10 (expanded) | 3 | Align to manifest |

All other stacks (27) match. Fix the 3 headers during implementation.

If #150 (agent-side resolution from manifest) lands, headers may be
removed entirely — but that is a separate decision.

### Pattern files: removed from dependency graph

Pattern files (`*-patterns.md`) contain implementation recipes — factory
pattern, gate job structure, rate limiting setup. These describe well-known
software engineering patterns that any capable LLM already knows from
training data. Agent context files need conventions ("use factory
pattern for test data"), not tutorials on what a factory pattern is.

**Decision:** remove all 5 pattern files from the manifest and dependency
graph. Move them to `docs/patterns/` as human reference documentation.

| Pattern file | Move to | Parent keeps |
|-------------|---------|-------------|
| `base/testing-patterns.md` | `docs/patterns/testing.md` | One-line summary in `## Patterns` |
| `base/cicd-patterns.md` | `docs/patterns/cicd.md` | One-line summary in `## Patterns` |
| `base/devsecops-patterns.md` | `docs/patterns/devsecops.md` | One-line summary in `## Patterns` |
| `base/security-patterns.md` | `docs/patterns/security.md` | One-line summary in `## Patterns` |
| `frontend/patterns.md` | `docs/patterns/frontend.md` | One-line summary in `## Patterns` |

Each parent rules file retains a `## Patterns` section with a one-line
list of which patterns to use — the convention. The full recipe lives in
`docs/patterns/` for human readers browsing GitHub.

This eliminates:
- 5 manifest entries and their `depends_on` chains
- All pattern resolution logic (auto-convention, includes, subset constraint)
- ~1700 lines from agent context
- The `devsecops-patterns → cicd` transitive edge case

### Resolution algorithm

With patterns removed, the resolution algorithm is four steps:

```
RESOLVE(manifest, stack_id, extras, platform_id):
  resolved = {}
  files = []
  1. for id in manifest.core:  ADD(id)           # core tier
  2. RESOLVE_DEPS(stack_id)                       # stack chain
  3. for id in extras:         RESOLVE_DEPS(id)   # project extras
  4. RESOLVE_DEPS(platform_id)                    # platform chain
  return files

ADD(id):
  if id in resolved: return
  resolved.add(id)
  files.append(manifest.lookup(id).file)

RESOLVE_DEPS(id):
  if id in resolved: return
  entry = manifest.lookup(id)
  for dep in entry.depends_on:
    RESOLVE_DEPS(dep)
  ADD(id)
```

No pattern step, no branching beyond dedup. Core → stack → extras →
platform. All steps except core use `RESOLVE_DEPS` — if deps are
already resolved, the recursion short-circuits with zero cost.

Manifest schema for core tier:

```yaml
version: "1.0"
core: [base-quality, base-git, base-docs, base-readme, base-testing]
```

Top-level list. Smoke tests validate all IDs in `core:` exist in the
manifest.
