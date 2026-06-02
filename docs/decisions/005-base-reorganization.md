---
id: 005
status: Accepted
date: 2026-05-04
category: templates
supersedes: []
superseded_by: []
---

# ADR-005: Apply Miller's law to repository structure

## Context

Miller's law (7±2): humans can hold roughly 7 items in working
memory. Folder listings that exceed this range force sequential
scanning instead of recognition.

### Root level: 12 directories

The repository has 12 top-level directories — above 7±2. Six are
template source, six are project infrastructure:

| Template source | Project infrastructure |
|-----------------|----------------------|
| base/ | docs/ |
| backend/ | tests/ |
| frontend/ | tools/ |
| stack/ | examples/ |
| platform/ | generated/ |
| formats/ | assets/ |

A newcomer cannot tell at a glance what is the product vs what
supports the product.

### base/ level: 23 files

`base/` contains 23 files covering concerns from git conventions to
360-degree analysis. Usage analysis against all 29 stacks:

| Tier | Files | Stack usage |
|------|-------|-------------|
| Universal (all 29 stacks) | git, docs, quality | 3 |
| Language (11 stacks) | typescript | 1 |
| Single stack | testing, devsecops, cicd, issues, scope | 5 |
| Never resolved (extras only) | 14 remaining files | 0 |

14 of 23 files are never pulled in by any stack's dependency chain.
They exist as opt-in extras, but nothing in the folder structure
signals this. A 23-item flat list exceeds 7±2 by 3x.

## Decision

Two changes, both applying Miller's law.

### 1. Nest template source under templates/

Group the 6 template directories under a single `templates/` parent:

```
templates/
  base/
  backend/
  frontend/
  stack/
  platform/
  formats/
```

Root level goes from 12 directories to 7: `templates/`, `docs/`,
`tests/`, `tools/`, `examples/`, `generated/`, `assets/`. Within
7±2. `templates/` has 6 children — also within 7±2.

### 2. Split base/ into subfolders

Split `base/` into 5 subfolders grouped by concern:

```
templates/base/
  core/       # Foundation — applies to every project
  security/   # Application and pipeline security
  infra/      # CI/CD, containers, deployment, release
  workflow/   # Session protocol, issues, analysis, gates
  language/   # Language-specific and data concerns
```

### File mapping

#### core/ (6 files)

| File | Description |
|------|-------------|
| `git.md` | Committer identity, commits, branching, PR workflow |
| `docs.md` | Rule language, documentation standards, ADR |
| `quality.md` | Architecture, code style, testing |
| `testing.md` | Test pyramid, coverage, naming conventions |
| `readme.md` | README structure, badges, quick start |
| `review.md` | Peer review priority, checklists |

#### security/ (4 files, 2 after ADR-004 pattern move)

| File | Description |
|------|-------------|
| `security.md` | Application security rules |
| `security-patterns.md` | Application security patterns |
| `devsecops.md` | Pipeline security (SAST, SCA, SBOM) |
| `devsecops-patterns.md` | Pipeline security patterns |

#### infra/ (5 files, 3 after ADR-004 pattern move)

| File | Description |
|------|-------------|
| `cicd.md` | Pipeline stages, triggers, environments |
| `cicd-patterns.md` | Reusable CI/CD patterns |
| `containers.md` | Dockerfile, runtime security, Kubernetes |
| `deployment.md` | Deploy targets, certs, LB, registries |
| `release.md` | Semver, version bump, backward compat |

#### workflow/ (5 files)

| File | Description |
|------|-------------|
| `scope.md` | Scope guard, session protocol |
| `issues.md` | Issue templates (epic, task, bug, spike) |
| `quality-gates.md` | Three-layer gate model, thresholds |
| `ai-workflow.md` | AI-assisted development lifecycle |
| `360.md` | 360-degree project analysis |

#### language/ (2 files)

| File | Description |
|------|-------------|
| `typescript.md` | Type design, naming, strictness |
| `data-quality.md` | Data sourcing, completeness, scoring |

### Subfolder sizes

| Subfolder | Now | After ADR-004 |
|-----------|-----|---------------|
| core | 6 | 6 |
| security | 4 | 2 |
| infra | 5 | 3 |
| workflow | 5 | 5 |
| language | 2 | 2 |
| **Total** | **22** | **18** |

All subfolders stay within the 7±2 range.

### Impact on manifest.yaml

All entries update their `file:` path to include `templates/` prefix
and (for base entries) the subfolder:

```yaml
# Before
- id: base-git
  file: base/git.md

# After
- id: base-git
  file: templates/base/core/git.md
```

IDs stay the same. Only `file:` fields change. The `depends_on`
lists reference IDs, not paths, so they need no changes.

### Impact on file headers

`[DEPENDS ON: ...]` headers in template files reference file paths.
These update to the new paths:

```markdown
# Before
[DEPENDS ON: base/quality.md]

# After
[DEPENDS ON: templates/base/core/quality.md]
```

### Impact on agents

Agents resolve files from `manifest.yaml` using the `file:` field.
The resolution algorithm is unchanged — only the path strings differ.
Agents never browse folders directly.

## Alternatives considered

1. **Top-level split without templates/** (`core/`, `security/`,
   `infra/` as top-level folders). Rejected: explodes the top level
   from 12 to 16+ directories.

2. **core/ + extras/** (two-way base split). Rejected: `extras/`
   is a junk drawer. "Everything else" provides no navigational
   signal. A reader still scans 17 files.

3. **Keep flat, rely on naming** (prefix files like
   `security-*.md`). Rejected: prefixes help sorting but don't
   reduce the item count. 23 files is still 23 files.

4. **templates/ without base subfolders**. Rejected: solves the
   root level but leaves the 23-file `base/` problem untouched.

5. **base subfolders without templates/**. Rejected: solves `base/`
   but the root stays at 12 directories. Both problems should be
   addressed together.

## Consequences

- Root goes from 12 directories to 7 — within 7±2
- `base/` goes from 23 items to 5 subfolders — within 7±2
- All manifest `file:` paths change (mechanical — `templates/`
  prefix + base subfolder)
- All `[DEPENDS ON]` headers update to new paths (mechanical)
- `SPEC.md` directory listing updates (generated by sync.py)
- `tools/sync.py` needs no logic changes — it reads manifest paths
- Smoke tests pass without changes — they validate manifest paths
  against filesystem
- If ADR-004 lands first, pattern files move to `docs/patterns/`
  before this reorganization, reducing base file count to 18
- If this lands first, ADR-004 moves patterns from their new
  subfolder paths — order doesn't matter
