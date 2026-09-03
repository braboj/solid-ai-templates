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
or similar).

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
the available stacks, then follow the [DEPENDS ON] chain for
the stack that fits.
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
git submodule add https://github.com/braboj/solid-ai-templates.git .ai-templates
```

1. Open your agent in your project directory
2. Tell the agent to read `.ai-templates/templates/INTERVIEW.md`
3. Follow the interview — the agent reads templates from the
   submodule and generates your context file
4. Commit the generated file alongside the submodule

To update templates: `git submodule update --remote`. Then
re-run the interview to regenerate your context file with the
latest rules.

## Model limitations

<!-- generated:readme-model-limits -->
| Stack category | Stacks | Largest chain | Prompt | Min context |
|----------------|--------|---------------|--------|-------------|
| abstract | 2 | `stack-python-service` — 444K chars | ~127K tokens | 200K |
| backend | 8 | `stack-django` — 458K chars | ~131K tokens | 200K |
| embedded | 1 | `stack-c-embedded` — 271K chars | ~77K tokens | 128K |
| hypermedia | 1 | `stack-htmx` — 283K chars | ~81K tokens | 128K |
| library | 3 | `stack-python-lib` — 371K chars | ~106K tokens | 128K |
| static | 2 | `stack-tutorial` — 411K chars | ~117K tokens | 200K |
<!-- /generated:readme-model-limits -->

Measured rather than estimated. Each row takes the largest resolved
chain in that category — the file under `generated/` an adopter
attaches — and converts it at 3.5 characters per token, a rate held
below the four-per-token rule of thumb because Markdown carrying
tables, fenced code and hyphenated identifiers tokenizes worse than
prose. The minimum window adds 18K tokens for the interview and the
file the model has to write back, then rounds up to the next window a
model actually sells.

`py tools/sync.py` regenerates the table from the chains and
`py tools/sync.py --check` fails when it drifts, so the figures move
when a base template grows instead of ageing quietly.

- **Output token limit < 16K** (e.g. GPT-4o default): generated file
  may be truncated — generate section by section or set `max_tokens`
  to the model maximum
- **Output token limit 32K+**: full inline file fits in one pass

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

## Supported agents

| Agent | Output file |
|-------|-------------|
| Claude Code | `CLAUDE.md` |
| Codex CLI, Devin, Cursor, Windsurf | `AGENTS.md` |

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
