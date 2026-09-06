# SOLID-AI Templates

*Forged in real work, not theorized — every rule here came from a real
AI-assisted project.*

You've shipped the same CLAUDE.md three times this quarter. Each copy is
slightly different, none of them are right, and the agent still doesn't
know your team's conventions.

You're not alone, and it's not negligence — writing context files from
scratch is the quiet cost of every agent-assisted team. Everyone pays
it, few teams have a system for it, and the codebase drifts a little
further from your standards every sprint.

This repo gives you composable templates that codify your team's
conventions once — base rules, stack rules, company rules — and feed
them to every agent on every project. Tax paid. Move on.

Back to the work that actually moves the product. The spikes, the design
conversations, the reviews that catch bugs instead of churning style nits.

## What it does

- Build `CLAUDE.md` or `AGENTS.md` from reusable layers — base, backend/frontend, stack
- Fork and extend — layer your team's conventions on the base without modifying it
- Codify industry standards — 12-factor app, OWASP, SOLID, SemVer, conventional commits
- Assemble templates you need, override if needed or create new ones

## How to use

**Prerequisites:** a local coding agent that can read files from
your project directory (Claude Code, Cursor, Codex CLI, Windsurf,
or similar). The optional `tools/` scripts also need Python 3 and
PyYAML (`pip install pyyaml`); commands below use `python3`, which
on Windows is `py`.

**Output:** a `CLAUDE.md` or `AGENTS.md` file placed at your project
root, containing coding conventions tailored to your stack. Works
for new projects and refactoring alike — the context file describes
how code *should be written*, giving your agent a consistent target
whether starting from scratch or improving existing code. Review and
adjust the output before adopting it — results vary by model and
prompt size.

### Try it — clone and point the agent at the templates

*Fastest path. The agent picks the stack on its own — least
input from you, most variance in output.*

Clone the repo and tell the agent to generate from it:

```bash
git clone https://github.com/braboj/solid-ai-templates.git
```

1. Open your agent in your project directory
2. Tell the agent:

```
Use solid-ai-templates/ to generate a CLAUDE.md for this
project. Start by reading templates/manifest.yaml to discover
the available stacks. Load every id in its core: list, then
follow the [DEPENDS ON] chain for the stack that fits. The
resolver seeds the core tier and no [DEPENDS ON] declares it,
so the chain alone misses it.
```

3. The agent picks a matching stack, resolves the chain, and
   drafts the file
4. Review, adjust, and place at your project root

### Use it — clone and run the interview

*Guided path. The agent asks about your project before generating —
slower, but tighter fit to your context.*

Clone the templates and let the agent guide you through setup:

```bash
git clone https://github.com/braboj/solid-ai-templates.git
```

1. Open your agent in your project directory
2. Tell the agent to read `solid-ai-templates/templates/INTERVIEW.md`
3. The agent asks about your project, proposes a stack, and reads
   the relevant templates
4. Confirm the stack — the agent generates `CLAUDE.md` or `AGENTS.md`
5. Place the generated file at your project root

The interview tends to produce a tighter fit than the
manifest-discovery path, because the agent gathers project
specifics from you before resolving the dependency chain (base
rules, layer rules, stack rules). Results depend on the model and
context window available.

### Adopt it — vendor as a submodule

For teams that want version-pinned templates inside their repo:

```bash
cd my-project
git submodule add https://github.com/braboj/solid-ai-templates.git docs/solid-ai-templates
```

1. Open your agent in your project directory
2. Tell the agent to read `docs/solid-ai-templates/templates/INTERVIEW.md`
3. Follow the interview — the agent reads templates from the
   submodule and generates your context file
4. Commit the generated file alongside the submodule

To update templates: `git submodule update --remote`. Then
re-run the interview to regenerate your context file with the
latest rules.

## Model limitations

Template updates are selective: adopt new conventions for a project need or
material risk, not merely because a tag exists. Existing adopted rules remain
effective; declining a new rule needs no ADR or ticket. See the
[consumer migration guidance](docs/PLAYBOOK.md#adopt-a-template-policy-update).

<!-- generated:readme-model-limits -->
| Stack category | Stacks | Largest chain | Prompt | Min context |
|----------------|--------|---------------|--------|-------------|
| abstract | 2 | `stack-python-service` — 457K chars | ~130K tokens | 200K |
| backend | 8 | `stack-django` — 471K chars | ~134K tokens | 200K |
| embedded | 1 | `stack-c-embedded` — 276K chars | ~79K tokens | 128K |
| hypermedia | 1 | `stack-htmx` — 289K chars | ~83K tokens | 128K |
| library | 3 | `stack-python-lib` — 382K chars | ~109K tokens | 128K |
| static | 2 | `stack-tutorial` — 419K chars | ~120K tokens | 200K |
<!-- /generated:readme-model-limits -->

Measured rather than estimated. Each row takes the largest resolved
chain in that category — the file under `generated/` an adopter
attaches — and converts it at 3.5 characters per token, a rate held
below the four-per-token rule of thumb because Markdown carrying
tables, fenced code and hyphenated identifiers tokenizes worse than
prose. The minimum window adds 18K tokens for the interview and the
file the model has to write back, then rounds up to the next window a
model actually sells.

`python3 tools/sync.py` regenerates the table from the chains and
`python3 tools/sync.py --check` fails when it drifts, so the figures move
when a base template grows instead of ageing quietly.

- **Output token limit < 16K** (e.g. GPT-4o default): generated file
  may be truncated — generate section by section or set `max_tokens`
  to the model maximum
- **Output token limit 32K+**: full inline file fits in one pass

## What a project picks

A project does not pick one template. It picks a **stack**, a **platform**,
and any **extras** it needs, and each one resolves independently: the core
tier plus that template's own `[DEPENDS ON]` tree. An extra is guaranteed
nothing from the stack it sits beside, which is why it can be added to any
of them.

```
your project
  |-- one stack        python-fastapi, go-service, htmx, ...
  |-- one platform     github, gitlab, linear
  `-- any extras       caching, jobs, release, deployment, ...
```

`python3 tools/resolve.py --roots` lists every root a project can pick. The
stacks are below; the rest are the extras table that follows them.

<!-- generated:readme-root-counts -->
Measured: 17 stacks and 20 orthogonal templates, 37 roots in all. An extra
resolves to the 6 core-tier files plus 1 to 5 of its own.
<!-- /generated:readme-root-counts -->

## Supported stacks

<!-- generated:readme-stacks -->
| Template | Layer | Description |
|----------|-------|-------------|
| `templates/stack/htmx.md` | hypermedia | HTMX 2.x, Alpine.js, SSE, OOB swaps, partial responses |
| `templates/stack/static-site-astro.md` | static | Islands architecture, client directives, content collections |
| `templates/stack/static-site-tutorial.md` | static | Multi-chapter tutorial, diagrams, CC BY-NC-SA |
| `templates/stack/python-lib.md` | library | Installable package or CLI tool, mypy, ruff, pytest |
| `templates/stack/python-service.md` | abstract | Generic Python web service, SQLAlchemy, Alembic |
| `templates/stack/python-flask.md` | backend | Sync REST API, factory pattern, blueprints |
| `templates/stack/python-fastapi.md` | backend | Async REST API, Pydantic v2, DI, OpenAPI |
| `templates/stack/python-django.md` | backend | Full web framework, ORM, DRF, admin |
| `templates/stack/go-lib.md` | library | Importable library or CLI binary |
| `templates/stack/go-service.md` | abstract | Generic Go HTTP service, chi, structured logging |
| `templates/stack/go-echo.md` | backend | REST API, Echo v4, middleware, validation |
| `templates/stack/node-express.md` | backend | Minimal REST API, Zod validation, Supertest |
| `templates/stack/node-nestjs.md` | backend | Modules, controllers, providers, guards, pipes, DI |
| `templates/stack/go-grpc.md` | backend | gRPC service, bufconn, errgroup |
| `templates/stack/python-grpc.md` | backend | gRPC service, grpcio-aio, proto design |
| `templates/stack/nodejs-lib.md` | library | TypeScript npm package or CLI, tsup, Vitest |
| `templates/stack/c-embedded.md` | embedded | GCC + CMake, Unity tests, HAL, binary + .a |
<!-- /generated:readme-stacks -->

## Platforms and extras

Picked independently of the stack, each resolving as its own root. The
examples under `examples/` cite several of these, so a reader who opens one
meets templates the stacks table does not list.

<!-- generated:readme-extras -->
| Template | Kind | Description |
|----------|------|-------------|
| `templates/backend/caching.md` | backend | Cache-aside, TTL, invalidation, resilience, stampede |
| `templates/backend/edge.md` | backend | Reverse proxy / edge — TLS termination, forwarded headers, upstream routing, timeouts, edge security |
| `templates/backend/jobs.md` | backend | Background jobs, idempotency, retry, DLQ, scheduling |
| `templates/backend/microservices.md` | backend | Service boundaries, inter-service comms, saga, contract testing |
| `templates/backend/monitoring.md` | backend | Key metrics, thresholds, alerts, dashboards, incidents |
| `templates/backend/webhooks.md` | backend | Inbound webhook intake, edge signature verification, fast-ack, retry amplification |
| `templates/base/workflow/360.md` | workflow | 360-degree project analysis — four stakeholder perspectives, grading |
| `templates/base/core/agents.md` | core | Output structure, models (inline/reference/hybrid), formatting rules |
| `templates/base/workflow/ai-workflow.md` | workflow | AI-assisted development lifecycle, work item hierarchy |
| `templates/base/workflow/communication.md` | workflow | Communication preferences — concise output, shorthand verbs, scope-asking |
| `templates/base/workflow/compression.md` | workflow | Re-verifying summaries, tables and rollups derived from verified research |
| `templates/base/data/data-governance.md` | data | Classification, PII handling, retention, ownership, audit trail |
| `templates/base/data/data-migration.md` | data | Versioned migrations, zero-downtime, rollback strategies |
| `templates/base/infra/deployment.md` | infra | Deployment targets (cloud/hybrid/offline), certs, LB, registries, secrets |
| `templates/base/workflow/release.md` | workflow | Semver, version bump propagation, backward compat, cut-over |
| `templates/base/core/skills.md` | core | Skill authoring — when to write one, frontmatter, triggering, structure, scripts |
| `templates/base/workflow/two-pass-review.md` | workflow | Split convention checks into mechanical (auto-fix) and contextual (over-flag, judge) passes over one catalogue |
| `templates/platform/github.md` | platform | CodeQL, GitHub Actions, gitleaks action, push protection |
| `templates/platform/gitlab.md` | platform | Semgrep OSS, GitLab CI/CD, gitleaks CLI |
| `templates/platform/linear.md` | platform | Label groups, native priority, sub-issues, code-host sync |
<!-- /generated:readme-extras -->

`generated/` holds a pre-resolved chain for each stack and none for these.
A stack chain spans dozens of files and is tedious to assemble by hand,
which is what a pre-resolved file is for; an extra brings a handful at
most, so reading the template and the core tier is the shorter path.
Attach the template directly, or run `python3 tools/resolve.py <root>
--concat` to get its chain the same way.

## Supported agents

<!-- generated:readme-agents -->
| Agent | Output file |
|-------|-------------|
| Claude Code | `CLAUDE.md` |
| Cursor | `.cursor/rules/project.mdc` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| OpenAI Codex CLI | `AGENTS.md` |
| Generic / other | `AI_CONTEXT.md` |
<!-- /generated:readme-agents -->

See `templates/base/core/agents.md` for structure, models, and formatting rules.

## Links

- [System design and composition rules](docs/SPEC.md)
- [Changelog](CHANGELOG.md)
- [Project status and roadmap](https://github.com/braboj/solid-ai-templates/milestones)
- [Example generated context files](examples/)
- [Onboarding guide](docs/ONBOARDING.md)
- [Operational playbook](docs/PLAYBOOK.md)
- [Architecture decision records](docs/decisions/)
- [How to contribute](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Report an issue](https://github.com/braboj/solid-ai-templates/issues)

## License

[CC BY 4.0](LICENSE) — Creative Commons Attribution 4.0 International.
You are free to use, share, and adapt the templates for any purpose,
including commercial use, as long as you give attribution.

## Author

[Branimir Georgiev](https://github.com/braboj) — [Imbra.io](https://imbra.io)
