# Onboarding

Welcome to solid-ai-templates. This guide gets a new contributor from zero
to first PR.

## What this project is

A composable, SOLID-inspired template system for generating AI agent context
files. Instead of writing a `CLAUDE.md` or `AGENTS.md` from scratch for every
project, you compose templates from three layers:

```
templates/base/       → rules that apply to every project
templates/backend/    → rules for backend services and APIs
templates/frontend/   → rules for frontend and UI projects
templates/stack/      → concrete, technology-specific rules
```

An agent reads the relevant templates, asks a short interview, and outputs
a ready-to-use context file for Claude Code, Cursor, Copilot, or Codex CLI.

Read `docs/SPEC.md` for the full composition model before contributing.

## Prerequisites

- Git
- A Markdown editor (any)
- Python 3.x — for running the structural smoke tests and the
  conformance runner
- GitHub CLI (`gh`), authenticated — for the issue, pull-request and
  release steps in `docs/PLAYBOOK.md`, and for the conformance checks
  that read milestones, labels and workflow runs. Without it those
  checks fail rather than skip, since a check that cannot reach its
  subject has not verified it
- An AI agent for validation (Claude Code recommended) — for E2E tests

## First steps

```bash
git clone https://github.com/braboj/solid-ai-templates.git
cd solid-ai-templates
```

No build step — all templates are plain Markdown, so nothing is compiled
and nothing is packaged. The checks are the exception and do take a
dependency: they need Python and PyYAML, `pip install pyyaml`. Without it
the smoke runner refuses the run and names what is missing rather than
reporting the 14 manifest-reading checks as failures.

Set up pre-commit hooks for local validation:
```bash
pip install pre-commit
pre-commit install
```

## Understand the structure

| File / folder | Read this to understand |
|---------------|------------------------|
| `docs/SPEC.md` | The full composition model — inheritance, OVERRIDE, EXTEND, IDs |
| `CLAUDE.md` | Rules for contributing to this repo |
| `templates/manifest.yaml` | Machine-readable dependency graph |
| `tools/resolve.py` | Dependency resolver — resolves a stack's full template chain |
| `generated/` | Pre-resolved template chains — one file per stack |
| `examples/` | Complete generated CLAUDE.md files — the target output |

## How templates relate

Every stack template starts with `[DEPENDS ON: ...]` listing its parent
templates. Read those parent templates first — the stack only adds or overrides
what differs from the parent.

Example chain:
```
templates/base/core/git.md + templates/base/core/quality.md + ...
    ↓
templates/stack/python-lib.md
    ↓
templates/stack/python-service.md
    ↓
templates/stack/python-flask.md
```

To see the full resolved chain for any stack, run:
```bash
py tools/resolve.py stack-flask          # print file list
py tools/resolve.py stack-flask --concat # print concatenated content
```

Or read the pre-resolved file directly: `generated/stack-flask.md`

## Validate your understanding

First, run the structural smoke tests to confirm the repo is in good shape:

```bash
py tests/run_smoke.py
```

Then run the checks the templates themselves prescribe, against this
repository — it is a consumer of its own base tier:

```bash
py tests/run_conformance.py
```

Both runners end with a `VERDICT:` line, printed after the report path so
that reading the last line alone cannot report success over a failed run.
A conformance run is not clean until any reading it lists is read: the
counts cover the automatic verdicts only.

Then run the system end-to-end with an agent:

1. Open Claude Code in any project directory
2. Attach `templates/INTERVIEW.md` and `templates/stack/python-flask.md`
3. Ask: "Generate a CLAUDE.md for this project using templates/base/core/agents.md
   format"
4. Review the output — this is what users get

Or use the automated E2E runner:

```bash
py tests/run_e2e.py STK-11   # Flask stack
```

## Making your first contribution

See `docs/PLAYBOOK.md` for step-by-step instructions on adding templates,
fixing content, and submitting a PR.

## Conventions to know before you write

- Rules use RFC 2119 keywords: MUST, MUST NOT, SHOULD, MAY
- Every section that another template might reference needs `[ID: ...]`
- Stack files follow the `<prefix>-<name>.md` naming convention (see `CLAUDE.md`)
- `templates/manifest.yaml` must be updated whenever a file is added, removed, or
  renamed

## Maintainership

This project has a bus factor of 1 — Branimir Georgiev is the sole
author and maintainer. The mitigation is documentation: everything
needed to understand, maintain, and extend the project is in the
repository (docs/SPEC.md, CLAUDE.md, PLAYBOOK.md, ADRs in docs/decisions/,
dev journal). No oral knowledge transfer is required.

If the maintainer becomes unavailable, the project can be forked and
continued from the repository alone.

## Getting help

- `docs/SPEC.md` — answers most "how does X work" questions
- Open an issue if something is unclear — Discussions are not enabled
