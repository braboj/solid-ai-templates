# Tests

Procedure specifications for solid-ai-templates following the
Imbra Procedure Specification Standard.

Spec files live in `tests/specs/`. See `CODIFICATION.md` for the ID scheme, area codes,
and component group registry.

## Specs

| ID | Type | Priority | Title |
|----|------|----------|-------|
| `SAIT-SMK-SYS-01-001A` | SMK | P0 | All DEPENDS ON file paths resolve to existing files |
| `SAIT-SMK-SYS-02-001A` | SMK | P0 | All section IDs are unique across all templates |
| `SAIT-SMK-SYS-03-001A` | SMK | P0 | Every template file has a corresponding manifest entry |
| `SAIT-SMK-SYS-04-001A` | SMK | P0 | DEPENDS ON headers match manifest depends_on |
| `SAIT-SMK-SYS-05-001A` | SMK | P1 | End-of-session audit is inlined verbatim or hard-delegated, never paraphrased |
| `SAIT-SMK-SYS-06-001A` | SMK | P1 | Every usable stack's resolved chain carries the MUST sections |
| `SAIT-SMK-SYS-07-001A` | SMK | P2 | 360 audit reports live only under docs/audits/ |
| `SAIT-SMK-SYS-08-001A` | SMK | P2 | Every showcased stack keeps its example CLAUDE.md |
| `SAIT-SMK-SYS-09-001A` | SMK | P2 | sync.py --check inspects without writing |
| `SAIT-SMK-SYS-10-001A` | SMK | P2 | A quoted DEPENDS ON in prose is not a declaration |
| `SAIT-SMK-TPL-04-001A` | SMK | P1 | All EXTEND and OVERRIDE directives reference existing IDs |
| `SAIT-INT-TPL-01-001A` | INT | P0 | DEPENDS ON chain assembles a complete rule set |
| `SAIT-INT-TPL-02-001A` | INT | P1 | EXTEND adds rules without removing base rules |
| `SAIT-INT-TPL-03-001A` | INT | P1 | OVERRIDE replaces parent section entirely |
| `SAIT-INT-TPL-05-001A` | INT | P1 | Conflicting OVERRIDEs on the same ID are flagged or resolved |
| `SAIT-INT-TPL-06-001A` | INT | P1 | EXTEND/OVERRIDE targets are reachable in the resolved chain |
| `SAIT-INT-TPL-07-001A` | INT | P2 | EXTEND sections do not duplicate parent rules |
| `SAIT-SMK-TPL-08-001A` | SMK | P1 | Every base template has at least one [ID:] tag |
| `SAIT-SMK-TPL-09-001A` | SMK | P1 | No empty [ID:] sections |
| `SAIT-SMK-ADR-01-001A` | SMK | P1 | ADR frontmatter matches the ADR-010 schema |
| `SAIT-INT-MNF-01-001A` | INT | P0 | All manifest entries reference valid paths and IDs |
| `SAIT-INT-MNF-02-001A` | INT | P0 | All stacks resolve to valid, non-empty file lists |
| `SAIT-INT-MNF-03-001A` | INT | P0 | All resolved chains include core tier files |
| `SAIT-INT-MNF-04-001A` | INT | P1 | Prompt builds for all stacks |
| `SAIT-INT-MNF-05-001A` | INT | P0 | resolve.py resolution matches the PyYAML resolution |
| `SAIT-INT-ITV-01-001A` | INT | P0 | All REQUIRED interview questions are asked before output is generated |
| `SAIT-INT-ITV-02-001A` | INT | P1 | DEFAULTED sections are pre-filled from the selected stack template |
| `SAIT-INT-ITV-03-001A` | INT | P0 | Interview answers override stack and base template rules in the output |
| `SAIT-E2E-STK-01-001A` | E2E | P0 | Full interview → CLAUDE.md for a FastAPI project |
| `SAIT-E2E-STK-02-001A` | E2E | P0 | Full interview → CLAUDE.md for a Go Echo project |
| `SAIT-E2E-FMT-01-001A` | E2E | P1 | Full interview → CLAUDE.md output format (Claude Code) |
| `SAIT-E2E-FMT-02-001A` | E2E | P1 | Full interview → AGENTS.md output format (Codex CLI) |
| `SAIT-E2E-STK-03-001A` | E2E | P1 | Full interview → CLAUDE.md for a Django project |
| `SAIT-E2E-STK-04-001A` | E2E | P1 | Full interview → CLAUDE.md for a Node Express project |
| `SAIT-E2E-STK-07-001A` | E2E | P1 | Full interview → CLAUDE.md for an Astro static site project |
| `SAIT-E2E-STK-08-001A` | E2E | P1 | Full interview → CLAUDE.md for a Go gRPC service |
| `SAIT-E2E-STK-10-001A` | E2E | P1 | Full interview → CLAUDE.md for a Go library project |
| `SAIT-E2E-STK-11-001A` | E2E | P1 | Full interview → CLAUDE.md for a Flask project |
| `SAIT-E2E-STK-12-001A` | E2E | P2 | Full interview → CLAUDE.md for a generic Python service |
| `SAIT-E2E-STK-13-001A` | E2E | P1 | Full interview → CLAUDE.md for a Python gRPC service |
| `SAIT-E2E-STK-15-001A` | E2E | P1 | Full interview → CLAUDE.md for a Python library project |
| `SAIT-E2E-STK-16-001A` | E2E | P2 | Full interview → CLAUDE.md for a generic Go service |
| `SAIT-E2E-STK-18-001A` | E2E | P1 | Full interview → CLAUDE.md for a Node.js library project |
| `SAIT-E2E-STK-20-001A` | E2E | P1 | Full interview → CLAUDE.md for an HTMX project |
| `SAIT-E2E-STK-21-001A` | E2E | P1 | Full interview → CLAUDE.md for a NestJS project |
| `SAIT-E2E-STK-22-001A` | E2E | P1 | Full interview → CLAUDE.md for a C embedded project |
| `SAIT-E2E-STK-23-001A` | E2E | P1 | Full interview → CLAUDE.md for a tutorial site project |
| `SAIT-E2E-DPL-01-001A` | E2E | P1 | Cloud deployment target produces correct deployment rules |
| `SAIT-E2E-DPL-02-001A` | E2E | P1 | Hybrid deployment target produces correct deployment rules |
| `SAIT-E2E-DPL-03-001A` | E2E | P1 | Offline deployment target produces correct deployment rules |
