# Starfield Blog

> **MANDATORY STARTUP — DO THIS BEFORE YOUR FIRST RESPONSE**
>
> You MUST read every file listed below IN FULL using the Read tool before
> you respond to the user's first message. No exceptions. Do not summarize,
> skip, or defer. These files contain binding conventions that this CLAUDE.md
> inherits. If you respond without reading them, you are violating project rules.
>
> 1. `docs/solid-ai-templates/base/quality.md`
> 2. `docs/solid-ai-templates/base/typescript.md`
> 3. `docs/solid-ai-templates/base/review.md`
> 4. `docs/solid-ai-templates/base/scope.md`
> 5. `docs/solid-ai-templates/base/git.md`
> 6. `docs/solid-ai-templates/base/docs.md`
> 7. `docs/solid-ai-templates/base/readme.md`
> 8. `docs/solid-ai-templates/base/issues.md`
> 9. `docs/solid-ai-templates/frontend/quality.md`
> 10. `docs/solid-ai-templates/frontend/ux.md`
> 11. `docs/solid-ai-templates/frontend/static-site.md`
> 12. `docs/solid-ai-templates/stack/static-site-astro.md`

Personal blog about astronomy and astrophotography. Static site with
content collections and zero client-side JS.

- Model: hybrid

Quality conventions defined in `docs/solid-ai-templates/` (submodule).
Project-specific overrides and additions follow below.


## 1. Project

### 1.1 Identity

- **Name**: starfield-blog
- **Owner**: Alex Rivera
- **Repo**: github.com/arivera/starfield-blog
- **URL**: starfield.blog
- **Deployment**: GitHub Pages via GitHub Actions

### 1.2 Stack

- Language: TypeScript (strict mode)
- Framework: Astro 4 (output: static)
- Content: Astro Content Collections (Markdown + frontmatter)
- CSS: plain CSS with custom properties
- Package manager: npm
- Formatter: Prettier with `prettier-plugin-astro`

### 1.3 Project structure

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

```
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

### 2.2 TypeScript

- `strict: true` — no exceptions
- No `any` — use `unknown` and narrow
- No enums — use `as const` objects or string literal unions

### 2.3 Content rules

- One Markdown file per post in `src/content/posts/`
- Frontmatter must include: title, date, tags, description
- Image alt text is required — no decorative images without `alt=""`
- No inline HTML in Markdown posts


## 3. Quality

### 3.1 SEO

- JSON-LD structured data for BlogPosting
- Open Graph meta tags on all pages
- Canonical URLs
- `robots.txt` and auto-generated sitemap


## 4. Identity

### 4.1 Design

- Dark background with deep blue accent
- Minimal layout — content-first
- No stock photography — only original astrophotos

### 4.2 Brand voice

- Educational and enthusiastic
- Technical but accessible to hobbyists
- First person, conversational tone


## 5. Review process

### 5.1 Code review

Follow `base/review.md` priority order. Apply `base/quality.md` and
`base/typescript.md` as the standard.

### 5.2 Structure audit

Verify MUSTs from `base/docs.md`, `base/readme.md`, `base/git.md`,
`frontend/static-site.md`, and `stack/static-site-astro.md`.


## 6. Session protocol

Follow `base/scope.md` for the scope guard and end-of-session audit.

### 6.1 Start of session

Read `base/scope.md` (Session startup) and the mandatory startup block.

### 6.2 During the session

Follow `base/scope.md` (During work) — stay within the agreed scope.

### 6.3 End of session

On "wrap up" / "close out", read `base/scope.md` (End of session audit)
and execute each item sequentially; do not summarize or skip. Print the
checklist and mark each item done before moving to the next.
