# Interview Template

<!--
INSTRUCTIONS FOR THE AGENT
============================
Follow the four phases below in order. Ask one question at a time.
Always state your preference when asking a clarifying question.
Complete all four phases. Do not skip phases.
-->

---

## Phase 1 - Explore

Understand what the user wants to build. Do not ask about technology yet.
Focus on the problem, the users, and the goals.

Ask one question at a time. Suggested questions (pick the most relevant):

- What are you building, and who is it for?
- What problem does it solve?
- What are the key things the system needs to do?

---

## Phase 2 - Clarify

Ask 2-3 targeted follow-up questions to resolve ambiguity before proposing
a stack. Always state your preference as the default. Examples:

- "Will this be deployed to the cloud, or do you have on-prem constraints?
  I'd default to cloud."
- "Do you have a language or framework preference, or should I choose?
  I'd go with Python + FastAPI for a backend service like this."
- "Solo project or a team? I ask because it affects how much convention
  detail to include - I'd assume solo for now."

---

## Phase 3 - Propose

Based on what you learned, propose a complete setup:

- Language and version
- Framework
- Database and libraries (if applicable)
- Auth mechanism (if applicable)
- Deployment target and distribution
- Key conventions: testing, linting, git

Present the proposal as a short summary and ask the user to confirm or
adjust. Proceed to Phase 4 once the user approves.

---

## Phase 4 - Generate

Before generating, collect any missing fields in a single question:

- Project name (if not mentioned during the conversation)
- Owner (person, team, or organisation)
- Repository URL (e.g. github.com/acme/my-service)
- Output filename: `CLAUDE.md` (Claude Code) or `AGENTS.md`
  (all others)? I'd default to `CLAUDE.md`.
- **Inline, reference, or hybrid?** "Should I inline all rules, reference
  solid-ai-templates as a submodule, or use a hybrid (inline critical rules,
  reference the rest)? I'd default to inline for a single project, hybrid
  if you plan to use the templates across multiple projects."

### Inline model (default)

Select the matching stack template from the table below and load its
DEPENDS ON chain. If you have shell access, run
`py tools/resolve.py <stack-id> --concat` to get the full resolved
content. Otherwise, read the pre-resolved file from `generated/<stack-id>.md`.
Apply any adjustments from Phase 3.
Generate the output file using the format rules in `templates/base/core/agents.md`.
All rules are inlined — the output file is self-contained.
The user should review and adjust the output before adopting it.
End the file with: `<!-- Generated with solid-ai-templates (github.com/braboj/solid-ai-templates) -->`

Also generate `docs/ONBOARDING.md` and `docs/PLAYBOOK.md` following the
required structures in `templates/base/core/docs.md`.

### Reference model

Generate a leaner agent file that references the templates instead of
inlining them. The output file:

1. Points to `docs/solid-ai-templates/` as a submodule for base quality,
   review, and language-specific rules
2. Lists the relevant template files for this project's stack
3. Defines code review and structure audit scopes (which templates to
   read for each)
4. Contains only project-specific overrides and additions inline

End the file with: `<!-- Generated with solid-ai-templates (github.com/braboj/solid-ai-templates) -->`

Tell the user to add the submodule:
```
git submodule add https://github.com/braboj/solid-ai-templates.git docs/solid-ai-templates
```

Also generate `docs/ONBOARDING.md` and `docs/PLAYBOOK.md` following the
required structures in `templates/base/core/docs.md`.

### Hybrid model

Generate an agent file that inlines critical rules and references the
templates for the rest. Follow the hybrid model structure in
`templates/base/core/agents.md`. The output file:

1. Points to `docs/solid-ai-templates/` as a submodule
2. Lists ALL template files in the dependency chain
3. Inlines git conventions, project structure, language-specific
   safety rules, and content rules
4. References quality framework, review process, testing, a11y,
   SEO, and CI/CD from the templates
5. Renders §6.3 (end-of-session audit) by inlining `scope.md`'s
   checklist verbatim or hard-delegating ("execute each item; do not
   summarize") — never paraphrased into bullets (see `agents.md` §6.3)

End the file with: `<!-- Generated with solid-ai-templates (github.com/braboj/solid-ai-templates) -->`

Tell the user to add the submodule:
```
git submodule add https://github.com/braboj/solid-ai-templates.git docs/solid-ai-templates
```

Also generate `docs/ONBOARDING.md` and `docs/PLAYBOOK.md` following the
required structures in `templates/base/core/docs.md`.

<!-- generated:interview-stacks -->
| If the project is... | Use... | What it covers |
|----------------------|--------|----------------|
| HTMX + server rendering | `templates/stack/htmx.md` | HTMX 2.x, Alpine.js, SSE, OOB swaps, partial responses |
| Astro (static site) | `templates/stack/static-site-astro.md` | Islands architecture, client directives, content collections |
| Astro tutorial site | `templates/stack/static-site-tutorial.md` | Multi-chapter tutorial, diagrams, CC BY-NC-SA |
| React SPA | `templates/stack/spa-react.md` | Client-side app, TypeScript, RTL, a11y |
| Next.js (full-stack) | `templates/stack/full-nextjs.md` | App Router, Server/Client Components, API routes |
| Python library / CLI | `templates/stack/python-lib.md` | Installable package or CLI tool, mypy, ruff, pytest |
| Python service (no framework) | `templates/stack/python-service.md` | Generic Python web service, SQLAlchemy, Alembic |
| Python + Flask | `templates/stack/python-flask.md` | Sync REST API, factory pattern, blueprints |
| Python + FastAPI | `templates/stack/python-fastapi.md` | Async REST API, Pydantic v2, DI, OpenAPI |
| Python + Django | `templates/stack/python-django.md` | Full web framework, ORM, DRF, admin |
| Go library / CLI | `templates/stack/go-lib.md` | Importable library or CLI binary |
| Go service / API | `templates/stack/go-service.md` | Generic Go HTTP service, chi, structured logging |
| Go + Echo | `templates/stack/go-echo.md` | REST API, Echo v4, middleware, validation |
| Vue SPA | `templates/stack/spa-vue.md` | Client-side app, Composition API, Pinia, Vitest |
| Svelte SPA | `templates/stack/spa-svelte.md` | Client-side app, Svelte 5 runes, Vitest |
| SvelteKit (full-stack) | `templates/stack/full-sveltekit.md` | File-based routing, form actions, SSR |
| Hugo (static site) | `templates/stack/static-site-hugo.md` | Go templates, archetypes, content structure |
| Node.js + Express | `templates/stack/node-express.md` | Minimal REST API, Zod validation, Supertest |
| Node.js + NestJS | `templates/stack/node-nestjs.md` | Modules, controllers, providers, guards, pipes, DI |
| Java + Spring Boot | `templates/stack/java-spring-boot.md` | REST API, JPA, Spring Security, Flyway |
| Python + Celery | `templates/stack/python-celery-worker.md` | Background tasks, retry/backoff, Beat scheduling |
| Go + gRPC | `templates/stack/go-grpc.md` | gRPC service, bufconn, errgroup |
| Python + gRPC | `templates/stack/python-grpc.md` | gRPC service, grpcio-aio, proto design |
| Java + gRPC | `templates/stack/java-grpc.md` | gRPC service, grpc-java lifecycle |
| React Native (mobile) | `templates/stack/mobile-react-native.md` | iOS/Android, Expo, file-based routing, Maestro |
| Flutter (mobile) | `templates/stack/mobile-flutter.md` | iOS/Android, Riverpod, go_router, freezed |
| Terraform (IaC) | `templates/stack/iac-terraform.md` | Infrastructure as code, modules, remote state |
| Node.js library / CLI | `templates/stack/nodejs-lib.md` | TypeScript npm package or CLI, tsup, Vitest |
| Rust library / CLI / crate | `templates/stack/rust-lib.md` | Rust crate or CLI, thiserror/anyhow, crates.io |
| Embedded C (bare metal) | `templates/stack/c-embedded.md` | GCC + CMake, Unity tests, HAL, binary + .a |
<!-- /generated:interview-stacks -->
