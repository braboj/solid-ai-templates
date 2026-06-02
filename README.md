# SOLID-AI Templates

*Forged in real work, not theorized — every rule here came from a real
AI-assisted project. See
[ADR-011](docs/decisions/011-provenance-principle.md).*

Five developers with five agents produce five coding styles — unless they
share the same context file.

Your AI agent writes better code when it has good instructions — but most
teams write CLAUDE.md and AGENTS.md files from scratch, and they quickly
fall out of sync.

This repo gives you composable, SOLID-inspired templates for building
consistent context files for any stack and any agent.

## What it does

- Build `CLAUDE.md` or `AGENTS.md` from reusable layers — base, backend/frontend, stack
- Cover Python, Go, Java, Node, Rust, mobile, and DevOps stacks
- Output `CLAUDE.md` for Claude Code or `AGENTS.md` for Cursor, Copilot, Codex CLI
- Codify industry standards — 12-factor app, OWASP, SOLID, SemVer, conventional commits
- Run a 360-degree project assessment across four perspectives
- Enforce standardized issue labels, quality gates, and review processes

## How to use

**Prerequisites:** any LLM interface — local agent (Claude Code,
Cursor, Codex CLI), web portal (Claude.ai, ChatGPT, Gemini), or
REST API (Anthropic, OpenAI).

**Output:** a `CLAUDE.md` or `AGENTS.md` file placed at your project
root, containing coding conventions tailored to your stack. Works
for new projects and refactoring alike — the context file describes
how code *should be written*, giving your agent a consistent target
whether starting from scratch or improving existing code. Review and
adjust the output before adopting it — results vary by model and
prompt size.

### Try it — attach one file

No install required. Download a stack template from GitHub and attach
it to your agent:

1. Find your stack in the [supported stacks](#supported-stacks) table
2. Open the raw file on GitHub and save it (or copy the contents)
3. Open your agent in your project directory
4. Attach the stack template and provide your project details:

```
Attach: python-fastapi.md

Generate a CLAUDE.md for this project.
Name: my-service, owner: Acme, repo: github.com/acme/my-service,
database: PostgreSQL, auth: JWT.
```

The agent drafts a context file. Review it, adjust as needed, and
place it at your project root.

> **Web portal or API?** Use a pre-resolved file from `generated/`
> instead of a single stack template — it includes the full
> dependency chain in one file. See
> [model limitations](#model-limitations) for token guidance.

### Use it — clone and run the interview

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

The interview tends to produce more complete output than attaching a
single file, because the agent resolves the full dependency chain
(base rules, layer rules, stack rules). Results depend on the model
and context window available.

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

| Stack category | Prompt size | Min context window |
|----------------|-------------|-------------------|
| Library / CLI | ~12K tokens | 32K |
| Static site | ~15K tokens | 32K |
| Backend service | ~25–50K tokens | 128K |
| Full-stack | ~40–60K tokens | 128K |

- **Output token limit < 16K** (e.g. GPT-4o default): generated file
  may be truncated — generate section by section or set `max_tokens`
  to the model maximum
- **Output token limit 32K+**: full inline file fits in one pass
- **Free tier rate limits**: use a local agent or a pre-resolved file
  to minimise round trips

## Supported stacks

<!-- generated:readme-stacks -->
| Template | Layer | Description |
|----------|-------|-------------|
| `templates/stack/htmx.md` | hypermedia | HTMX 2.x, Alpine.js, SSE, OOB swaps, partial responses |
| `templates/stack/static-site-astro.md` | static | Islands architecture, client directives, content collections |
| `templates/stack/static-site-tutorial.md` | static | Multi-chapter tutorial, diagrams, CC BY-NC-SA |
| `templates/stack/spa-react.md` | frontend | Client-side app, TypeScript, RTL, a11y |
| `templates/stack/full-nextjs.md` | full-stack | App Router, Server/Client Components, API routes |
| `templates/stack/python-lib.md` | library | Installable package or CLI tool, mypy, ruff, pytest |
| `templates/stack/python-service.md` | abstract | Generic Python web service, SQLAlchemy, Alembic |
| `templates/stack/python-flask.md` | backend | Sync REST API, factory pattern, blueprints |
| `templates/stack/python-fastapi.md` | backend | Async REST API, Pydantic v2, DI, OpenAPI |
| `templates/stack/python-django.md` | backend | Full web framework, ORM, DRF, admin |
| `templates/stack/go-lib.md` | library | Importable library or CLI binary |
| `templates/stack/go-service.md` | abstract | Generic Go HTTP service, chi, structured logging |
| `templates/stack/go-echo.md` | backend | REST API, Echo v4, middleware, validation |
| `templates/stack/spa-vue.md` | frontend | Client-side app, Composition API, Pinia, Vitest |
| `templates/stack/spa-svelte.md` | frontend | Client-side app, Svelte 5 runes, Vitest |
| `templates/stack/full-sveltekit.md` | full-stack | File-based routing, form actions, SSR |
| `templates/stack/static-site-hugo.md` | static | Go templates, archetypes, content structure |
| `templates/stack/node-express.md` | backend | Minimal REST API, Zod validation, Supertest |
| `templates/stack/node-nestjs.md` | backend | Modules, controllers, providers, guards, pipes, DI |
| `templates/stack/java-spring-boot.md` | backend | REST API, JPA, Spring Security, Flyway |
| `templates/stack/python-celery-worker.md` | backend | Background tasks, retry/backoff, Beat scheduling |
| `templates/stack/go-grpc.md` | backend | gRPC service, bufconn, errgroup |
| `templates/stack/python-grpc.md` | backend | gRPC service, grpcio-aio, proto design |
| `templates/stack/java-grpc.md` | backend | gRPC service, grpc-java lifecycle |
| `templates/stack/mobile-react-native.md` | mobile | iOS/Android, Expo, file-based routing, Maestro |
| `templates/stack/mobile-flutter.md` | mobile | iOS/Android, Riverpod, go_router, freezed |
| `templates/stack/iac-terraform.md` | DevOps | Infrastructure as code, modules, remote state |
| `templates/stack/nodejs-lib.md` | library | TypeScript npm package or CLI, tsup, Vitest |
| `templates/stack/rust-lib.md` | library | Rust crate or CLI, thiserror/anyhow, crates.io |
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
- [Project status and roadmap](https://github.com/braboj/solid-ai-templates/milestones)
- [Example generated context files](examples/)
- [Onboarding guide](docs/ONBOARDING.md)
- [Operational playbook](docs/PLAYBOOK.md)
- [Architecture decision records](docs/decisions/)
- [Report an issue](https://github.com/braboj/solid-ai-templates/issues)

## License

[CC BY 4.0](LICENSE) — Creative Commons Attribution 4.0 International.
You are free to use, share, and adapt the templates for any purpose,
including commercial use, as long as you give attribution.

## Author

[Branimir Georgiev](https://github.com/braboj) — [Imbra.io](https://imbra.io)
