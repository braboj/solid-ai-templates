# Starfield Blog

Personal blog about astronomy and astrophotography. Static site with
content collections and zero client-side JS.

> Generation inputs (per ADR-016 — examples are agent-generated
> outputs of the documented pipeline):
>
> - Stack source: `templates/stack/static-site-astro.md`
> - Resolved chain: `generated/stack-astro.md` (base + frontend +
>   static-site-astro)
> - Platform: `templates/platform/github.md` — the second axis, which
>   follows from where the repository is hosted and not from the stack
> - Output format: `templates/base/core/agents.md` (hybrid model)
> - Project brief: Starfield Blog — Alex Rivera — astronomy /
>   astrophotography blog — TypeScript strict / Astro 4 (static) /
>   Content Collections / plain CSS — npm, Prettier, ESLint, astro
>   check — GitHub Pages via GitHub Actions

Quality conventions live in the `solid-ai-templates` submodule, vendored
at `docs/solid-ai-templates/`. Template files keep their upstream layout
under `templates/`, so a rule file referenced below resolves to
`docs/solid-ai-templates/templates/<layer>/<file>.md`. Project-specific
overrides and additions follow below.

> **MANDATORY STARTUP — DO THIS BEFORE YOUR FIRST RESPONSE**
>
> This file is hybrid: the damage-prone rules (git, TypeScript safety,
> content, session protocol) are inlined below, but the full quality
> framework lives in the referenced templates. You MUST read every file
> listed below IN FULL using the Read tool before you respond to the
> user's first message. No exceptions. Do not summarize, skip, or defer.
> If you respond without reading them, you are violating project rules.
>
> 1. `docs/solid-ai-templates/templates/base/core/quality.md`
> 2. `docs/solid-ai-templates/templates/base/language/typescript.md`
> 3. `docs/solid-ai-templates/templates/base/core/review.md`
> 4. `docs/solid-ai-templates/templates/base/workflow/scope.md`
> 5. `docs/solid-ai-templates/templates/base/core/git.md`
> 6. `docs/solid-ai-templates/templates/base/core/docs.md`
> 7. `docs/solid-ai-templates/templates/base/core/readme.md`
> 8. `docs/solid-ai-templates/templates/base/workflow/issues.md`
> 9. `docs/solid-ai-templates/templates/frontend/quality.md`
> 10. `docs/solid-ai-templates/templates/frontend/ux.md`
> 11. `docs/solid-ai-templates/templates/frontend/static-site.md`
> 12. `docs/solid-ai-templates/templates/stack/static-site-astro.md`
> 13. `docs/solid-ai-templates/templates/platform/github.md`

## Adoption boundary

- Templates supply candidate conventions; the project chooses what it adopts.
  Resolve dependencies to discover the available rules, not to authorize work.
- Adopt a new rule when it addresses a named local defect, requirement, or
  credible material risk. Preventive security controls need no prior incident.
- A template update MUST NOT automatically create compliance work, tickets,
  or decision records. A newer tag alone is not a reason to update the pin.
- A declined candidate needs at most a line in the existing PR or discussion;
  no ADR, separate ticket, or decline register is required.
- Existing adopted rules remain effective until the project changes them.
  Keep the operative selection and any necessary precedence in the project's
  context file; a reference/hybrid file MUST inline this adoption boundary so
  reading a new upstream MUST cannot silently expand the adopted rule set.
- Assess security fixes in tools the project executes promptly. Review new
  conventions when a project need warrants it, rather than on every release.

## 1. Project

### 1.1 Identity

- **Model**: hybrid
- **Name**: starfield-blog
- **Owner**: Alex Rivera
- **Repo**: github.com/arivera/starfield-blog
- **URL**: starfield.blog
- **Deployment**: GitHub Pages via GitHub Actions
- **Language**: TypeScript (strict mode)
- **Framework**: Astro 4 (output: static)
- **Content**: Astro Content Collections (Markdown + frontmatter)
- **CSS**: plain CSS with custom properties
- **Package manager**: npm
- **Formatter**: Prettier with `prettier-plugin-astro`

### 1.2 Project structure

```
src/
  content/
    posts/          # Markdown blog posts with frontmatter
    config.ts       # Content collection schemas
  components/
    layout/         # BaseLayout, Header, Footer
    ui/             # Card, Tag, Pagination
  pages/
    index.astro
    posts/[slug].astro
    tags/[tag].astro
  styles/
    global.css      # Custom properties, base styles, dark theme
public/
  images/           # Optimized astronomy photos
  favicon.svg
```

### 1.3 Commands

```bash
npm run dev       # develop at localhost:4321
npm run build     # production build to dist/
npm run preview   # preview production build
npm run lint      # ESLint
npm run check     # astro check
```

## 2. Code conventions

### 2.1 Git

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
- Always branch — never commit directly to `main`
- Branch naming: `feat/description`, `fix/description`
- PRs are small and focused — one concern per PR
- Never force-push a branch, including with `--force-with-lease`
- After a PR is merged, delete the branch and pull `main` before new work
- Do not commit `dist/`, `node_modules/`, or `.env`

### 2.2 TypeScript

- `strict: true` — no exceptions
- No `any` — use `unknown` and narrow
- No enums — use `as const` objects or string literal unions
- Type all content-collection schemas in `src/content/config.ts`

### 2.3 Content rules

- One Markdown file per post in `src/content/posts/`
- Frontmatter must include: title, date, tags, description
- Image alt text is required — no decorative images without `alt=""`
- No inline HTML in Markdown posts — no `set:html` on untrusted input

## 3. Quality

Read `docs/solid-ai-templates/templates/frontend/quality.md`,
`docs/solid-ai-templates/templates/frontend/ux.md`, and
`docs/solid-ai-templates/templates/frontend/static-site.md` for
accessibility, performance, and the static-site quality framework.
Inline only the SEO targets below.

### 3.1 SEO

- JSON-LD structured data for BlogPosting
- Open Graph meta tags on all pages
- Canonical URLs
- `robots.txt` and auto-generated sitemap

## 4. Identity

### 4.1 Design

- Dark background with deep blue accent — evokes the night sky
- Minimal, content-first layout — the photograph is the focal point
- No stock photography — only original astrophotos
- Generous whitespace; typographic hierarchy over decoration
- Respect `prefers-reduced-motion` — no autoplay or parallax

### 4.2 Brand voice

- Educational and enthusiastic — share the wonder, explain the science
- Technical but accessible to hobbyists — define jargon on first use
- First person, conversational tone
- Cite gear, settings, and capture conditions for each astrophoto

## 5. Review process

Follow `docs/solid-ai-templates/templates/base/core/review.md` priority
order. Apply `docs/solid-ai-templates/templates/base/core/quality.md`,
`docs/solid-ai-templates/templates/base/language/typescript.md`, and
`docs/solid-ai-templates/templates/frontend/quality.md` as the standard.
Verify MUSTs from `docs/solid-ai-templates/templates/base/core/docs.md`,
`docs/solid-ai-templates/templates/base/core/readme.md`,
`docs/solid-ai-templates/templates/base/core/git.md`,
`docs/solid-ai-templates/templates/frontend/static-site.md`,
`docs/solid-ai-templates/templates/stack/static-site-astro.md`, and
`docs/solid-ai-templates/templates/platform/github.md` for the
Actions workflow and the security tooling it maps.

## 6. Session protocol

Follow `docs/solid-ai-templates/templates/base/workflow/scope.md` for the
scope guard and end-of-session audit.

### 6.1 Start of session

Read `docs/solid-ai-templates/templates/base/workflow/scope.md` (Session
startup) and the mandatory startup block above. Confirm the scope with
the user before making changes.

### 6.2 During the session

Follow `docs/solid-ai-templates/templates/base/workflow/scope.md` (During
work) — stay within the agreed scope. Run `npm run check` and
`npm run lint` after any change; do not accumulate unverified changes.

### 6.3 End of session

On "wrap up" / "close out", read
`docs/solid-ai-templates/templates/base/workflow/scope.md` (End of
session audit) and execute each item sequentially; do not summarize or
skip. Print the checklist and mark each item done (with result) before
moving to the next. At minimum, confirm in order:

1. Commits and push — all changes committed and pushed (via PR if
   branch-protected)
2. Close issues — close completed issues; verify auto-close worked
3. Dev journal — add a session entry to `docs/dev-journal.md` (date,
   tool, key changes, PRs merged, issues closed/created)
4. ADRs — A consequential, durable architectural choice with meaningful alternatives
     MUST have an Architecture Decision Record (ADR) in `docs/decisions/` when
     future maintainers need its tradeoffs to safely reconsider it. Examples:
     ownership boundaries, compatibility contracts, or a major dependency strategy.
   Routine naming, formatting, directory creation, document moves, check-output
     refinements, and compliance repairs belong in the issue/PR and current docs.
     They need no ADR unless their consequences meet the threshold above; no
     separate justification for not writing an ADR is required.
5. CLAUDE.md — for each new convention, decide whether it belongs here
   (a rule the agent MUST apply every turn) or in another doc
6. README.md / docs — for each new command, dependency, or content
   rule, confirm it is reflected; name the section
7. Build and checks — run `npm run check` and `npm run build` and
   confirm both pass
8. Flag gaps — report any item that cannot be completed as pending,
   never as done, before closing
9. Summary — summarize what was done and what is next
