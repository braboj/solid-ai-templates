# Test Codification Scheme

Defines the procedure ID scheme for solid-ai-templates test specifications.
Follows the Imbra Procedure Specification Standard
(`imbra-knowledge/standards/PROCEDURE-SPECIFICATION.md`).

---

## ID format

```
{PRODUCT}-{TYPE}-{AREA}-{NN}-{NNN}{VER}
```

| Segment | Description |
|---------|-------------|
| `PRODUCT` | Product code — always `SAIT` |
| `TYPE` | Procedure type — `SMK`, `INT`, `E2E` |
| `AREA` | Functional area — `SYS`, `TPL`, `MNF`, `STK`, `FMT`, `ITV`, `DPL` |
| `NN` | Two-digit component group number — unique within an area |
| `NNN` | Three-digit sequence number within the group |
| `VER` | Version letter — `A` original, `B` first major revision |

---

## Product code

| Code | Product |
|------|---------|
| `SAIT` | solid-ai-templates |

---

## Procedure types

| Code | Type | Description |
|------|------|-------------|
| `SMK` | Smoke test | Quick structural health check — files exist, IDs unique, paths resolve |
| `INT` | Integration test | Verify two or more templates work together correctly |
| `E2E` | End-to-end test | Verify a complete interview → output generation flow |

---

## Areas

| Code | Area | Description |
|------|------|-------------|
| `SYS` | System | Cross-cutting structural checks spanning multiple concerns |
| `TPL` | Template | Template composition — DEPENDS ON chain, EXTEND, OVERRIDE directives |
| `STK` | Stack | Full interview → correct CLAUDE.md content per stack |
| `MNF` | Manifest | manifest.yaml consistency — IDs, file paths, dependency references |
| `FMT` | Format | Output format rendering — AGENTS.md, Cursor .mdc, Copilot, generic |
| `ITV` | Interview | Interview flow — required questions, defaults, answer precedence |
| `DPL` | Deployment | Deployment target scenarios — cloud, hybrid, offline |
| `ADR` | ADR governance | ADR file conventions — frontmatter schema, supersession links, status discipline |

---

## Component groups

Component group numbers are fixed per area. Once assigned, a number is never
reused for a different component within the same area.

### SYS - System

| Number | Component |
|--------|-----------|
| `01` | File structure — DEPENDS ON path resolution, file existence |
| `02` | ID uniqueness — section IDs across all templates |
| `03` | Manifest coverage — every template file has a manifest entry |
| `04` | Header–manifest sync — DEPENDS ON headers match manifest depends_on |
| `05` | Generation fidelity — end-of-session audit inlined verbatim or hard-delegated, never paraphrased |

### TPL - Template

| Number | Component |
|--------|-----------|
| `01` | DEPENDS ON — dependency chain assembly |
| `02` | EXTEND — additive directive behaviour |
| `03` | OVERRIDE — replacement directive behaviour |
| `04` | Reference resolution — EXTEND/OVERRIDE refs point to existing IDs |
| `05` | Conflict resolution — two templates OVERRIDE the same section ID |
| `06` | Chain reachability — EXTEND/OVERRIDE targets in resolved chain |
| `07` | Duplication — EXTEND sections do not restate parent rules |
| `08` | ID presence — base templates have at least one [ID:] tag |
| `09` | Section content — [ID:] sections are not empty |

### MNF - Manifest

| Number | Component |
|--------|-----------|
| `01` | Manifest entries — file paths, IDs, depends_on references |
| `02` | Resolution — all stacks resolve to valid, non-empty file lists |
| `03` | Core tier — resolved chains include core tier files |
| `04` | Prompt assembly — prompt builds for all stacks |

### STK - Stack

| Number | Component |
|--------|-----------|
| `01` | FastAPI — python-fastapi stack interview flow |
| `02` | Go Echo — go-echo stack interview flow |
| `03` | Django — python-django stack interview flow |
| `04` | Express — node-express stack interview flow |
| `05` | — retired (spa-react stack removed, v2.26) |
| `06` | — retired (full-nextjs stack removed, v2.26) |
| `07` | Astro — static-site-astro stack interview flow |
| `08` | Go gRPC — go-grpc stack interview flow |
| `09` | — retired (mobile-flutter stack removed, v2.26) |
| `10` | Go lib — go-lib stack interview flow |
| `11` | Flask — python-flask stack interview flow |
| `12` | Python service — python-service base stack |
| `13` | Python gRPC — python-grpc stack interview flow |
| `14` | — retired (python-celery-worker stack removed, v2.26) |
| `15` | Python lib — python-lib stack interview flow |
| `16` | Go service — go-service base stack |
| `17` | — retired (static-site-hugo stack removed, v2.26) |
| `18` | Node.js lib — nodejs-lib stack interview flow |
| `19` | — retired (rust-lib stack removed, v2.25) |
| `20` | HTMX — htmx stack interview flow |

### FMT - Output Format

| Number | Component |
|--------|-----------|
| `01` | AGENTS.md — OpenAI Codex CLI format |
| `02` | Cursor — .cursor/rules/project.mdc format |
| `03` | Copilot — .github/copilot-instructions.md format |
| `04` | Generic — AI_CONTEXT.md fallback format |

### ITV - Interview

| Number | Component |
|--------|-----------|
| `01` | Required questions — all REQUIRED questions asked before generation |
| `02` | Default sections — DEFAULTED sections pre-filled from templates |
| `03` | Precedence — interview answers override stack and base rules |

### DPL - Deployment Guidelines

| Number | Component |
|--------|-----------|
| `01` | Cloud — public cloud deployment target output |
| `02` | Hybrid — on-premises + cloud deployment target output |
| `03` | Offline — air-gapped deployment target output |

### ADR - ADR governance

| Number | Component |
|--------|-----------|
| `01` | Frontmatter schema — id, status, date, category, supersedes/superseded_by validity and reciprocal links |

---

## Version suffix

| Suffix | Meaning |
|--------|---------|
| `A` | Original version |
| `B` | First major revision (scope or assertions changed) |
| `C` | Second major revision |

Amend in place (no new suffix) for: typo fixes, wording clarifications,
corrected prerequisites where test intent is unchanged.

---

## Full ID examples

| ID | Meaning |
|----|---------|
| `SAIT-SMK-SYS-01-001A` | Smoke — system — file structure — spec 1, version A |
| `SAIT-SMK-SYS-02-001A` | Smoke — system — ID uniqueness — spec 1, version A |
| `SAIT-SMK-SYS-03-001A` | Smoke — system — manifest coverage — spec 1, version A |
| `SAIT-SMK-SYS-04-001A` | Smoke — system — header–manifest sync — spec 1, version A |
| `SAIT-SMK-TPL-04-001A` | Smoke — composition — ref resolution — spec 1, version A |
| `SAIT-INT-TPL-01-001A` | Integration — composition — DEPENDS ON chain — spec 1, version A |
| `SAIT-INT-TPL-02-001A` | Integration — composition — EXTEND directive — spec 1, version A |
| `SAIT-INT-TPL-03-001A` | Integration — composition — OVERRIDE directive — spec 1, version A |
| `SAIT-INT-TPL-05-001A` | Integration — composition — conflict resolution — spec 1, version A |
| `SAIT-INT-TPL-06-001A` | Integration — composition — chain reachability — spec 1, version A |
| `SAIT-INT-TPL-07-001A` | Integration — composition — duplication — spec 1, version A |
| `SAIT-SMK-TPL-08-001A` | Smoke — composition — ID presence — spec 1, version A |
| `SAIT-SMK-TPL-09-001A` | Smoke — composition — section content — spec 1, version A |
| `SAIT-INT-MNF-01-001A` | Integration — manifest — manifest entries — spec 1, version A |
| `SAIT-INT-MNF-02-001A` | Integration — manifest — resolution — spec 1, version A |
| `SAIT-INT-MNF-03-001A` | Integration — manifest — core tier — spec 1, version A |
| `SAIT-INT-MNF-04-001A` | Integration — manifest — prompt assembly — spec 1, version A |
| `SAIT-INT-ITV-01-001A` | Integration — interview — required questions — spec 1, version A |
| `SAIT-INT-ITV-02-001A` | Integration — interview — default sections — spec 1, version A |
| `SAIT-INT-ITV-03-001A` | Integration — interview — answer precedence — spec 1, version A |
| `SAIT-E2E-STK-01-001A` | E2E — stack — FastAPI flow — spec 1, version A |
| `SAIT-E2E-STK-02-001A` | E2E — stack — Go Echo flow — spec 1, version A |
| `SAIT-E2E-FMT-01-001A` | E2E — format — CLAUDE.md format (Claude Code) — spec 1, version A |
| `SAIT-E2E-FMT-02-001A` | E2E — format — AGENTS.md format (Codex CLI) — spec 1, version A |
| `SAIT-E2E-FMT-03-001A` | E2E — format — Cursor format — spec 1, version A |
| `SAIT-E2E-FMT-04-001A` | E2E — format — Copilot format — spec 1, version A |
| `SAIT-E2E-FMT-05-001A` | E2E — format — Generic format — spec 1, version A |
| `SAIT-E2E-STK-03-001A` | E2E — stack — Django flow — spec 1, version A |
| `SAIT-E2E-STK-20-001A` | E2E — stack — HTMX flow — spec 1, version A |
| `SAIT-E2E-DPL-01-001A` | E2E — deployment — cloud scenario — spec 1, version A |
| `SAIT-E2E-DPL-02-001A` | E2E — deployment — hybrid scenario — spec 1, version A |
| `SAIT-E2E-DPL-03-001A` | E2E — deployment — offline scenario — spec 1, version A |
