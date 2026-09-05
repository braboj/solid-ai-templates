# Maria Chen — Portfolio

Personal portfolio and blog for a product designer — showcases
selected work, writing, and contact information.

- Owner: Maria Chen
- Repo: github.com/mariachen/portfolio
- Live URL: mariachen.design
- Deployment: GitHub Pages via GitHub Actions on push to `main`
- Model: inline

> Generation inputs (per ADR-016 — examples are agent-generated
> outputs of the documented pipeline):
>
> - Stack source: `stack/static-site-astro.md`
> - Resolved chain: `generated/stack-astro.md` (base + frontend +
>   static-site-astro)
> - Output format: `base/core/agents.md` (inline model)
> - Project brief: Maria Chen — Portfolio — Maria Chen — Astro 4
>   (output: static) / zero client-side JS / plain CSS with custom
>   properties / JSON content in `src/data/` — npm, Prettier with
>   `prettier-plugin-astro` — GitHub Pages via GitHub Actions

This file is self-contained: all rules are inlined, no external
templates need to be read.

## 1. Project

### 1.1 Overview

- Model: inline
- Framework: Astro 4 (output: static)
- Interactive components: none — zero client-side JS, no islands
- CSS: plain CSS with custom properties — no framework
- Content: JSON files in `src/data/`
- Language: TypeScript (`.astro` frontmatter, build config)
- Package manager: npm
- Formatter: Prettier with `prettier-plugin-astro`
- Hosting: GitHub Pages, deployed via GitHub Actions on push to `main`

### 1.2 Project structure

```
src/
  components/
    layout/
      BaseLayout.astro      # <html>, <head>, global styles, footer
      Header.astro
      Footer.astro
    ui/
      ProjectCard.astro
      PostCard.astro
      Tag.astro
  pages/
    index.astro             # Home — hero, featured work, about snippet
    work/
      index.astro           # All projects grid
      [slug].astro          # Individual project case study
    writing/
      index.astro           # All posts list
      [slug].astro          # Individual blog post
    contact.astro
    404.astro               # Custom error page
  data/
    site.json               # Nav, hero text, social links, footer copy
    projects.json           # Work items — title, slug, tags, image, body
    posts.json              # Blog posts — title, slug, date, body
  styles/
    global.css              # CSS custom properties, resets, type scale
    tokens.css              # Colour, spacing, and font tokens
public/
  images/
    work/                   # Case study images — WebP, named by slug
    og/                     # Open Graph images — 1200x630 WebP
  fonts/                    # Self-hosted variable fonts (woff2)
  robots.txt
astro.config.mjs
prettier.config.mjs
eslint.config.js
package.json
README.md
CLAUDE.md
```

- Separation of content and code — all editable content lives in
  `src/data/` as JSON, never hardcoded in `.astro` files
- One stylesheet pair — tokens in `tokens.css`, everything else in
  `global.css`; no inline styles except dynamic/computed values
- `src/content/` is intentionally avoided — Astro reserves that path
  for Content Collections; migrate only when data outgrows JSON (see
  2.4)
- See `README.md` for the full project structure

### 1.3 Commands

```bash
npm run dev      # astro dev — hot reload at localhost:4321
npm run build    # astro build — production build to dist/
npm run preview  # astro preview — serve production build locally
npm run lint     # eslint .
npm run format   # prettier --check .
npm run check    # astro check — validate .astro files and types
npm run validate # lint + format + check + build — full quality gate
```

- `validate` composes the named scripts — each step is callable on
  its own and as part of the full gate
- Run `npm run build` (or `npm run validate`) locally before pushing —
  a failing build MUST NOT reach `main`

## 2. Code conventions

### 2.1 Git

- Branch: `main` (source of truth) — deploys automatically on push;
  never commit directly, always work on a branch
- Branch naming: `feat/<scope>`, `fix/<scope>`, `content/<scope>`,
  `chore/<scope>`
- Commits: `<type>(<scope>): <summary>` — types: content, feat, fix,
  style, chore; subject under 80 characters, imperative mood
- PRs are small and focused — one concern per PR
- Repeat the closing keyword before each issue number:
  `Closes #a, closes #b` — a bare `#b` stays open
- Never force-push a branch, including with `--force-with-lease`; when
  behind `main`, merge `main` in or use `gh pr update-branch`
- After a PR is merged, delete the branch and pull `main` before new
  work
- Always run `npm run dev` (and `npm run build` for a release) before
  committing
- Do not commit `dist/`, `node_modules/`, or `.DS_Store`
- Do not commit unoptimised images — compress to WebP before adding to
  `public/`
- Every repository MUST have a `.gitignore` and a committed lockfile

### 2.2 Astro and TypeScript

- Default to `.astro` components — they are static by default, ship
  zero JS
- This site has no interactive components — never use a `client:*`
  directive; all pages are fully static
- One concern per component — layout, UI primitives, and page sections
  are separate files
- TypeScript `strict: true` — no exceptions; follow
  `@typescript-eslint/recommended`
- No `any` — use `unknown` and narrow, or define a proper type
- Use `interface` for object shapes; `type` for unions and aliases;
  no enums — use `as const` objects or string literal unions
- Import types with `import type { ... }`; explicit return types on
  non-trivial functions
- MUST NOT use `set:html` — it bypasses Astro's escaping (the
  `innerHTML` equivalent); use `{expression}` for text content. The
  only acceptable exception is JSON-LD via `JSON.stringify()`, where
  the input is fully server-controlled (see 3.4)
- ESLint with `@typescript-eslint/recommended` and
  `eslint-plugin-sonarjs` for any `.ts` files — configured in
  `eslint.config.js`, run on save
- Prettier owns all formatting — `.astro` files use the official
  `prettier-plugin-astro`; no style debates in code review
- Source files UTF-8, ASCII content only, LF line endings

### 2.3 Content editing

- All editable text lives in `src/data/` JSON files — never hardcoded
  in `.astro`
- To add a project: add an entry to `projects.json` and its images to
  `public/images/work/`
- To add a post: add an entry to `posts.json` with the full Markdown
  body in the `body` field
- Never hardcode derived counts (project totals, post counts) — compute
  them from the data source

| File | Controls |
|------|----------|
| `src/data/site.json` | Nav links, hero text, footer copy, socials |
| `src/data/projects.json` | Work items — title, slug, tags, image, body |
| `src/data/posts.json` | Blog posts — title, slug, date, excerpt, body |

### 2.4 Content Collections (when data outgrows JSON)

- Migrate from `src/data/` JSON to Astro Content Collections when a
  single file exceeds ~200 entries / ~500 lines, entries need rich
  Markdown bodies, per-entry git diffs get hard to review, or a
  non-developer needs to author content
- Define collection schemas in `src/content.config.ts` using Zod;
  every field that affects rendering or sorting MUST be in the schema
- Use `z.enum()` for constrained values; mark optional fields with
  `.optional()`
- Query with `getCollection()` / `getEntry()` — never read files
  directly; sort and filter in the page component, not the data files
- The Zod schema MUST include a `description` field — layouts render
  it as the meta, OG, and Twitter Card description (see 3.3)

### 2.5 Styling

- All design tokens in `src/styles/tokens.css` as CSS custom
  properties — never use raw colour or spacing values in component
  styles
- All CSS in the global stylesheet pair — no inline styles except
  dynamic/computed values, no CSS-in-JS, no utility frameworks
- BEM-like naming: `.component-element` (e.g. `.hero-grid`,
  `.nav-link`)
- Mobile-first: base styles for mobile, `@media (min-width: 768px)`
  for tablet, `@media (min-width: 1200px)` for desktop
- Typography scale: use `--text-sm`, `--text-base`, `--text-lg`, etc.
  from tokens
- Self-host fonts as woff2 in `public/fonts/` with `@font-face` in CSS
  and `font-display: block` — never depend on an external font CDN at
  runtime
- Animation: a single `IntersectionObserver` in `BaseLayout.astro`
  handles `.reveal` -> `.reveal.visible` transitions — do not add
  per-component scripts
- Maximum line length 80 characters (exempt: prose strings,
  third-party URLs)

### 2.6 Assets

- Images in `public/images/` — reference as `/images/filename.webp`;
  no assets outside `public/` — Astro only serves static files from
  there
- All images MUST be WebP, compressed before committing
- Provide `width` and `height` attributes on every `<img>` to prevent
  layout shift
- OG images in `public/og/` at 1200x630 — one per page

## 3. Quality

### 3.1 Testing and quality gates

- This is a content site with no business logic — the build is the
  primary test: `npm run validate` (lint + format + check + build)
  MUST pass before every PR
- `astro check` validates `.astro` files, types, and any content
  schemas — zero errors before merge
- Quality gate map (editor -> pre-commit -> CI):

| Category | Tool | Config |
| --- | --- | --- |
| Lint | ESLint | `eslint.config.js` |
| Format | Prettier | `.prettierrc` |
| Type check | `astro check` / `tsc --noEmit` | `tsconfig.json` |
| Secrets | gitleaks (pre-commit + CI) | — |
| Build | `astro build` | — |
| Links | lychee (`--root-dir dist`) | `lychee.toml` |
| Site quality | Lighthouse CI | `lighthouserc.json` |

- Hook framework: `husky` + `lint-staged` — config in `package.json`
- Lighthouse thresholds: accessibility >= 90 (error); performance,
  SEO, best practices >= 90 (warn)
- lychee MUST use `--root-dir dist` to resolve root-relative paths
  (e.g. `/work`); without it every root-relative link reports a false
  error

### 3.2 Accessibility — WCAG 2.1 AA

- Target standard: WCAG 2.1 AA; minimum text contrast 4.5:1 (normal),
  3:1 (large)
- Semantic HTML: correct landmark elements and a single, ordered
  heading hierarchy per page
- Every `<img>` has descriptive `alt`; decorative images use `alt=""`
- Icon-only or ambiguous links MUST have a descriptive `aria-label`
- All `<a>` and nav links MUST have a visible `:focus-visible` outline
  — use `:focus-visible`, not `:focus`
- No content relies on colour alone to convey meaning
- Lighthouse accessibility score >= 90 on every page (CI error)

### 3.3 SEO

- `robots.txt` required, and it MUST allow answer-engine crawlers
  (OAI-SearchBot, ChatGPT-User, PerplexityBot, Claude-SearchBot /
  Claude-User, Applebot)
- `@astrojs/sitemap` MUST be installed as an Astro integration —
  generates the sitemap at build time, referenced in `robots.txt`
- Open Graph and Twitter Card meta tags required; canonical URL
  required on every page
- Every page MUST have a unique `description` — used for
  `<meta name="description">`, OG description, and Twitter Card; write
  it as a pitch ("why should I click?"), not a summary
- If `og:image` is present, `twitter:image` MUST also be present;
  include `og:image:width` / `og:image:height` (1200x630)
- H1 is unique per page and reflects its content; H1 keywords appear
  in the page body
- Privacy-friendly analytics only — no consent banner, no third-party
  tracking scripts without explicit consent

### 3.4 Structured data

- JSON-LD SHOULD be present on content pages in a
  `<script type="application/ld+json">` tag in the layout — render via
  `JSON.stringify()` with `set:html` (the acceptable exception to the
  `set:html` ban, since the input is server-controlled)
- Schema `@type` MUST match the page's actual role — use `Person` for
  the about/home, `CreativeWork` or `Article` for case studies and
  posts; do not use commerce types (`Product`, `Offer`) on an
  editorial portfolio

### 3.5 Performance and deployment

- Static generation by default — no client-side rendering
- Preload critical above-the-fold assets (hero image, primary font);
  defer any non-critical scripts
- Keep shipped JS at zero — the only script is the shared
  `IntersectionObserver` reveal handler
- Monitor Core Web Vitals (LCP, CLS, INP) — treat regressions as bugs
- Trailing slash: GitHub Pages forces trailing slashes — set
  `trailingSlash: "always"` in `astro.config.mjs` and enforce it across
  internal links, canonical URLs, and sitemap entries

## 4. Identity

### 4.1 Design

- Palette: off-white `#F9F8F6` background, near-black `#1A1A18` text,
  sage green `#6B8F71` accent — all defined as tokens in `tokens.css`
- Typography: "DM Sans" (variable, self-hosted) for body; "DM Serif
  Display" for headings
- Spacing scale: 4px base unit — spacing tokens in `tokens.css`
- Aesthetic: editorial, airy, generous whitespace — no heavy borders
  or shadows
- Never hardcode visual values — colour, spacing, and type always come
  from the tokens

### 4.2 Brand voice

- Tone: warm, direct, thoughtful — never corporate or salesy
- Write in first person — "I designed", "I led", not "The designer"
- Project descriptions lead with the problem, then the approach, then
  the outcome — no jargon
- Blog posts: conversational but substantive — aim for clarity over
  cleverness
- Lead each page section with a direct answer and keep paragraphs
  self-contained — answer engines retrieve passages, not whole pages

## 5. Review process

### 5.1 Code review

Before merging, review the diff against the base branch in priority
order (highest first):

1. Correctness — content lives in `src/data/`, no hardcoded copy or
   counts; no `client:*` directives; `width`/`height` on every image
2. Accessibility — semantic HTML, alt text, `:focus-visible` outlines,
   contrast holds; Lighthouse a11y >= 90
3. Clarity — names self-documenting, one concern per component
4. Conventions — ESLint and Prettier clean, no `set:html` (except
   server-controlled JSON-LD), tokens used for all visual values,
   lines under 80 characters

Confirm CI is green. Only merge after the review passes.

### 5.2 Structure audit

- Run `npm run validate` before every PR (lint + format + check +
  build)
- Verify `robots.txt`, the generated sitemap, canonical URLs, and a
  unique `description` exist for every page
- Verify every internal link uses a trailing slash and resolves under
  `dist/` (lychee with `--root-dir dist`)
- Verify `README.md` documents the commands and the content-editing
  guide
- Run the audit after: new project, a new page type, a Content
  Collections migration, or before a release

## 6. Session protocol

Follow `templates/base/workflow/scope.md` for scope guard and
end-of-session audit.

### 6.1 Start of session

1. Read this `CLAUDE.md` and `README.md` in full before the first
   change
2. Check the current branch — if not `main`, ask why before proceeding
3. Check `git status` — if uncommitted changes exist, ship the
   previous session's wrap (branch, commit, push, merge) before any
   new work
4. Clean up stale branches: `git fetch --prune`, then delete local
   branches whose PRs have merged
5. Check deploy health — verify the latest GitHub Pages deploy on
   `main` completed successfully; flag if stuck, failed, or pending
6. Confirm the scope with the user before making changes
7. If the task is ambiguous, ask: "What is the specific deliverable
   for this session?"
8. Review open issues related to the agreed scope before writing code

### 6.2 During the session

- Flag explicitly when a task grows beyond the agreed scope — do not
  silently absorb new requests
- Finishing and committing the current work takes priority over
  starting something new
- Run `npm run dev` (and `npm run build` for build-affecting changes)
  after every change — do not accumulate unverified changes
- When a tool (formatter, codemod, image optimiser) touches unrelated
  files, revert the drift before committing and file it separately

### 6.3 End of session

When the user signals end of session ("wrap up", "let's finish", "end
session", "close out", or similar), print the full checklist below and
execute each item sequentially. Mark each item done (with result)
before moving to the next. Do not batch, skip, or summarize — visible
sequential execution prevents missed steps.

1. Commits and push — all changes committed and pushed (via PR if
   branch-protected)
2. Close issues — close completed issues (verify auto-close worked)
3. Epic checklists — update epic checklists if relevant
4. Dev journal — add a session entry to `docs/dev-journal.md` (date,
   tool, key changes, PRs merged, issues closed/created)
5. ADRs — A consequential, durable architectural choice with meaningful alternatives
     MUST have an Architecture Decision Record (ADR) in `docs/decisions/` when
     future maintainers need its tradeoffs to safely reconsider it. Examples:
     ownership boundaries, compatibility contracts, or a major dependency strategy.
   Routine naming, formatting, directory creation, document moves, check-output
     refinements, and compliance repairs belong in the issue/PR and current docs.
     They need no ADR unless their consequences meet the threshold above; no
     separate justification for not writing an ADR is required.
6. CLAUDE.md — for each new convention, decide whether it belongs here
   (a rule the agent MUST apply every turn) or in another doc; keep
   each rule to one line
7. README.md — for each new command, dependency, or structural change,
   confirm it is reflected; name the section
8. docs/ONBOARDING.md — for each new tool, prerequisite, or setup step,
   confirm it is documented; name the section
9. docs/PLAYBOOK.md — for each new command, script, or workflow,
   confirm it is documented; name the section
10. Content and assets — confirm new images are WebP and compressed,
    and any new page has a unique `description`, canonical URL, and OG
    image
11. Build and quality gate — run `npm run validate` and confirm it
    passes
12. Flag gaps — if any item cannot be completed this session, report it
    as pending (never as done) before closing
13. Summary — summarize what was done and what is next
