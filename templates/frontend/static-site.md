# Frontend — Static Site
[ID: frontend-static-site]
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/security/security.md, templates/frontend/ux.md, templates/frontend/quality.md]

Abstract rules for any static site generated at build time and served as
plain HTML, CSS, and minimal JavaScript. Never used directly — always
extended by a framework-specific stack (Astro, Hugo, Eleventy, etc.).

---

## Stack
[ID: static-site-stack]

- Output: static HTML generated at build time
- Serving: CDN or plain web server — no server-side runtime required
- JavaScript: minimal and opt-in — zero-JS by default where possible

---

## Architecture principle
[ID: static-site-architecture]

```
data files  →  components  →  build output (HTML)
    ↑                               ↓
Edit here                    Deployed here
```

- Separation of content and code — editable content lives in a data directory
- Default to static components; only reach for an interactive framework when
  client-side state is genuinely required
- One stylesheet — no inline styles except dynamic/computed values

---

## Content structure
[ID: static-site-content]
[EXTEND: base-docs]

All editable content lives in a data directory as structured files (JSON,
YAML, or Markdown). Never hardcode content that a non-developer might want
to change.

| File | Controls |
|------|----------|
| `[data path]/site.[ext]` | Nav links, hero text, contact links, footer |
| `[data path]/[section].[ext]` | [what it controls] |

---

## Assets
[ID: static-site-assets]

- Images: `public/images/` — reference as `/images/filename.ext`
- Documents: `public/docs/` — reference as `/docs/filename.ext`
- No assets outside `public/` — only files in `public/` are served statically

---

## Pages
[ID: static-site-pages]

| Page     | Path    | Notes             |
|----------|---------|-------------------|
| Homepage | `/`     | All main sections |
| 404      | `/404`  | Custom error page |

---

## Code conventions
[ID: static-site-code]

- **ESLint** for any JS/TS code — configured in `eslint.config.js`, run on save
- **Prettier** owns all formatting — commit `.prettierrc`; no style debates
  in code review
- If no JS/TS is present in the project, skip ESLint

---

## CSS conventions
[EXTEND: frontend-quality]

- All CSS in a single global stylesheet
- Use CSS custom properties from `:root` for all colours and spacing
- BEM-like naming: `.component-element` (e.g. `.hero-grid`, `.nav-link`)
- No CSS-in-JS, no utility frameworks unless explicitly chosen in stack

---

## Typography
[ID: static-site-typography]

- Prefer system font stacks over web fonts — eliminates font FOUC and
  external dependencies:
  ```css
  --font-text: system-ui, -apple-system, sans-serif;
  --font-code: ui-monospace, "Cascadia Code", "Fira Code", monospace;
  ```
- If web fonts are required, self-host them as woff2 files in `public/fonts/`
  and declare `@font-face` in CSS — never depend on external CDNs at runtime
- Use `font-display: block` for self-hosted fonts to prevent layout shift

---

## Theme persistence
[ID: static-site-theme]

- If the site supports dark mode via a `data-theme` attribute, initialize
  the theme from `localStorage` in a `<script>` tag inside `<head>` —
  before any content renders:
  ```html
  <script>
    document.documentElement.setAttribute(
      "data-theme",
      localStorage.getItem("theme") || "light"
    );
  </script>
  ```
- MUST NOT set the theme in a body script or deferred module — this causes
  a visible flash from light to dark on every page load

---

## Performance
[EXTEND: frontend-quality]

- Preload critical above-the-fold assets (hero image, primary font)
- Static generation by default — no client-side rendering unless necessary
- Defer non-critical scripts

---

## Trailing slash
[ID: static-site-trailing-slash]

- MUST verify the trailing slash convention matches the hosting platform's
  behavior (e.g. GitHub Pages forces trailing slashes, Netlify and Vercel
  are configurable)
- SHOULD add a CI check that scans built HTML output for internal hrefs
  violating the convention

---

## SEO
[ID: static-site-seo]
[EXTEND: frontend-quality]

- `robots.txt` required
- Open Graph and Twitter Card meta tags required
- Canonical URLs required
- Sitemap MUST be generated at build time and referenced in `robots.txt`
- Every content page MUST have a unique `description` in frontmatter — used
  for `<meta name="description">`, OG description, and Twitter Card
- Meta descriptions MUST read as a pitch, not a summary — answer "why
  should I click this?"
- JSON-LD structured data SHOULD be present on content pages (Article,
  Course, or appropriate schema type)
- Privacy-friendly analytics only (no consent banner required)

### SEO strategy (structure audit)

- **Title-intent alignment** — page titles SHOULD match the queries users
  actually type (check GSC or keyword research); include the primary
  keyword, not just abbreviations or internal jargon; 50–60 characters
- **Internal linking** — related pages SHOULD link to each other (topical
  clusters); no orphan pages (every page reachable within 3 clicks from
  the homepage); content pages SHOULD average 3+ internal links
- **Content depth** — pages intended for indexing SHOULD exceed ~150 words;
  pages below threshold are either enriched or noindexed; no
  duplicate/near-duplicate thin pages