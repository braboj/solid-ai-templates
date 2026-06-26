# Stack — Astro (Static Site)
[DEPENDS ON: templates/frontend/static-site.md, templates/base/language/typescript.md, templates/base/workflow/quality-gates.md]

Extends the static site stack with Astro-specific rules.

---

## Stack
[OVERRIDE: static-site-stack]

- Framework: Astro (static site generator, output: static / GitHub Pages)
- Interactive components: [React / Vue / Svelte / plain JS / none] — islands
  only
- CSS: [plain CSS / Tailwind / CSS modules]
- Content: [JSON files in `src/data/` / CMS / Markdown / hardcoded]
- Deployed via GitHub Actions on push to `main`

---

## Project structure
[ID: astro-structure]

- `src/pages/` — file-based routes; each `.astro` file is a page
- `src/layouts/` — shared page shells (`<head>`, base HTML)
- `src/components/` — `.astro` components; interactive islands in
  `src/components/interactive/`
- `src/content/` — content collections (Markdown + schema in
  `src/content/config.ts`)
- `src/data/` — structured data (JSON) when not using content collections
- `public/` — static assets served as-is (favicon, `robots.txt`)
- `astro.config.mjs` — integrations, `trailingSlash`, and site URL

---

## Component architecture
[OVERRIDE: static-site-architecture]

- Default to `.astro` components — they are static by default, zero JS shipped
- Only reach for the chosen JS framework (React, Vue, Svelte) when client-side
  state is genuinely required
- Interactive components live in `src/components/interactive/`
- See `README.md` for the full project structure

## Astro islands (client directives)
- `client:visible` — below-the-fold components, defers hydration until in view
- `client:load` — above-the-fold components that must be interactive immediately
- `client:only` — avoid unless SSR is enabled; skips server rendering entirely
- Never hydrate a component that does not need interactivity

---

## Content structure
[OVERRIDE: static-site-content]

All editable content lives in `src/data/` as JSON.

| File | Controls |
|------|----------|
| `src/data/site.json` | Nav links, hero text, contact links, footer |
| `src/data/[section].json` | [what it controls] |

Note: `src/content/` is intentionally avoided — Astro reserves that path
for Content Collections. See the next section for when to migrate.

---

## Content Collections
[ID: astro-content-collections]

Use Astro Content Collections when data outgrows `src/data/` files:

### When to migrate
- A single data file exceeds ~200 entries or ~500 lines
- Entries need rich text (Markdown body, not just fields)
- Per-entry git diffs become hard to review in a single file
- Non-developers need to author or edit content

### Schema definition
- Define collection schemas in `src/content.config.ts` using Zod
- Every field that affects rendering or sorting MUST be in the schema
- Use `z.enum()` for constrained values, not free strings
- Mark optional fields explicitly with `.optional()`

### File structure
```
src/content/
  [collection]/
    entry-slug.md       # frontmatter + optional Markdown body
src/content.config.ts   # schema definitions
```

### Rendering patterns
- Query with `getCollection()` / `getEntry()` — never read files
  directly
- Sort and filter in the page component, not in the data files
- Use `render()` for Markdown body content — it returns compiled
  HTML with full remark/rehype pipeline support

### Migration checklist
1. Create `src/content.config.ts` with Zod schema matching existing
   data shape
2. Convert each entry to a Markdown file with typed frontmatter
3. Update components to use `getCollection()` instead of JSON imports
4. Verify build passes — Astro validates frontmatter against schema
   at build time
5. Delete the old `src/data/` files

### Single-source content pattern
[ID: astro-single-source-content]

When content MUST remain SSG-agnostic (e.g. tutorial chapters that
work as plain Markdown on GitHub, in ebooks, and in other SSGs), point
the content collection at an external directory instead of duplicating
files into `src/content/`.

**Setup:**

1. Set the glob loader `base` to the external directory:
   ```typescript
   // src/content.config.ts
   const docs = defineCollection({
     loader: glob({
       pattern: "**/*.md",
       base: "../chapters",  // relative to astro project root
     }),
     schema: z.object({ ... }),
   });
   ```

2. Add a remark plugin to rewrite cross-reference links at build time.
   Chapters use `[Link](02-slug.md)` for GitHub compatibility; the
   plugin rewrites to `../slug/` for Astro routing:
   ```typescript
   // src/plugins/remark-rewrite-links.ts
   import { visit } from "unist-util-visit";
   import type { Root, Link } from "mdast";

   const CHAPTER_LINK = /^(\d{2}-)(.+)\.md(#.*)?$/;

   export function remarkRewriteLinks() {
     return (tree: Root) => {
       visit(tree, "link", (node: Link) => {
         const match = node.url.match(CHAPTER_LINK);
         if (match) {
           node.url = `../${match[2]}/${match[3] || ""}`;
         }
       });
     };
   }
   ```

3. Register the plugin in `astro.config.mjs`:
   ```javascript
   import { remarkRewriteLinks } from
     './src/plugins/remark-rewrite-links.ts';

   export default defineConfig({
     markdown: {
       remarkPlugins: [remarkRewriteLinks],
     },
   });
   ```

4. In CI, create a symlink for shared assets if chapters reference
   them via relative paths:
   ```yaml
   - name: Create assets symlink
     run: >
       mkdir -p astro-site/src/content &&
       ln -s ../../../assets astro-site/src/content/assets
   ```

**Rules:**
- MUST NOT duplicate content files into `src/content/` — the external
  directory is the single source of truth
- The remark plugin MUST handle all link patterns used in the source
  Markdown (numbered prefixes, anchors)
- Image paths from the source directory MUST resolve correctly in both
  GitHub rendering and the Astro build

---

## Assets
[OVERRIDE: static-site-assets]

- Images: `public/images/` — reference as `/images/filename.ext`
- Documents: `public/docs/` — reference as `/docs/filename.ext`
- No assets outside `public/` — Astro only serves static files from there

---

## View Transitions
[ID: astro-view-transitions]

- SHOULD enable Astro View Transitions via `<ClientRouter />` from
  `astro:transitions` in the base layout — eliminates full-page flash
  between navigations; static site feels like a SPA with zero
  client-side routing JS (~244 bytes gzip overhead per page)
- When using `<ClientRouter />`, MUST NOT use `DOMContentLoaded` in
  page scripts — it only fires on full page loads, not on client-side
  navigations
- Use `astro:page-load` instead — it fires on every navigation
  including View Transitions
- Scripts in `<script>` tags (not `is:inline`) are re-executed on
  navigation by default; `is:inline` scripts are not
- Gracefully degrades to full page loads if JS is disabled — no
  framework lock-in

---

## Reveal animations
- Use a single `IntersectionObserver` script in the base layout for
  `.reveal` → `.reveal.visible` transitions
- Do not add per-component reveal scripts

---

## Code conventions

- **ESLint** with `@typescript-eslint/recommended` and
  `eslint-plugin-sonarjs` for any `.ts` / `.tsx` files —
  configured in `eslint.config.js`, run on save
- Enable `parserOptions.projectService` for type-checked linting — many
  `sonarjs` rules (e.g. `no-alphabetical-sort`) require type info and are
  silently inert without it; use `recommended` not `recommendedTypeChecked`
  (the latter enables `no-unsafe-*` rules that break on CSS module imports
  and Astro content collection types)
- `eslint-plugin-unicorn` SHOULD be added for rules not covered by sonarjs
  (e.g. `no-zero-fractions`, `prefer-number-properties`)
- **Prettier** owns all formatting — commit `.prettierrc`; no style debates
  in code review
- `.astro` files formatted with the official Prettier Astro plugin
- MUST NOT use `set:html` — it is Astro's equivalent of `innerHTML` and
  bypasses escaping; use `{expression}` for text content instead

---

## Testing
[ID: astro-testing]

A static site has no unit-test suite by default — "testing" means
verifying the built output. Each check below is enforced by the Quality
gates table:

- Build MUST succeed with zero errors: `astro build`, plus `astro check`
  for type and content-schema validation
- Internal and external links MUST resolve — `lychee` over `dist/`
  (`--root-dir dist`, so root-relative paths resolve)
- Lighthouse CI MUST meet budgets: accessibility ≥ 90 (error),
  performance / SEO / best practices ≥ 90 (warn)
- Add component or unit tests (e.g. vitest, single-run via `npm test`)
  only for non-trivial client scripts or content utilities

---

## Git conventions
[EXTEND: base-git]

- Do not commit `dist/` or `node_modules/`
- Always test with `npm run dev` before committing

---

## Commands

### Core (MUST)
```
npm run dev      # astro dev — hot reload at localhost:4321
npm run build    # astro build — production build to dist/
npm run preview  # astro preview — serve production build locally
npm run prepare  # husky — auto-installs git hooks on npm install
```

### Quality (SHOULD — omit if the tool is not in the stack)
```
npm run lint     # eslint .
npm run format   # prettier --check .
npm run check    # astro check — validate .astro files, types, content schemas
npm test         # test runner in single-run mode (e.g. vitest run)
npm run validate # lint + format + check + test + build — full quality gate
```

### Development (MAY)
```
npm run test:watch  # test runner in watch mode (e.g. vitest)
```

Rules:
- `validate` SHOULD compose named scripts: each step callable individually
  and as part of the full gate
- `test` MUST run in single-run mode (exit after completion) — watch mode
  belongs in `test:watch`
- `prepare` is an npm lifecycle hook — runs automatically after `npm install`
---

## Quality gates
[EXTEND: base-quality-gates]

| Category | Layer 1 (editor) | Layer 2 (pre-commit) | Layer 3 (CI) | Config |
|----------|-----------------|---------------------|-------------|--------|
| Lint | ESLint | ESLint | ESLint | `eslint.config.js` |
| Format | Prettier | Prettier | Prettier --check | `.prettierrc` |
| Type check | TypeScript | tsc --noEmit | tsc --noEmit | `tsconfig.json` |
| Security | — | — | Platform SAST | — |
| Secrets | — | gitleaks | gitleaks | — |
| Build | — | — | astro build | — |
| Links | — | — | lychee | `lychee.toml` |

- Lychee MUST use `--root-dir dist` to resolve root-relative
  paths (e.g. `/about`); without it, every root-relative link
  reports a false error
| Site quality | — | — | Lighthouse CI ≥ 90 | `lighthouserc.json` |

- Hook framework: `husky` + `lint-staged` — config in `package.json`
- Lighthouse thresholds: accessibility ≥ 90 (error), performance / SEO /
  best practices ≥ 90 (warn)

---

## Trailing slash
[EXTEND: static-site-trailing-slash]

- MUST set `trailingSlash` in `astro.config.mjs` to match hosting platform
  (`"always"` for GitHub Pages, `"never"` for Netlify/Vercel defaults)

---

## SEO
[EXTEND: static-site-seo]

- `@astrojs/sitemap` MUST be installed as an Astro integration — generates
  `sitemap-index.xml` at build time
- Content collections MUST include a `description` field in the Zod schema:
  ```typescript
  z.object({
    title: z.string(),
    description: z.string(),
    // ...
  })
  ```
- Layouts MUST render the description as `<meta name="description">`, OG
  description, and Twitter Card description
- JSON-LD structured data SHOULD be rendered in a `<script
  type="application/ld+json">`
  tag in the layout — use `JSON.stringify()` with `set:html` (acceptable
  exception to the `set:html` ban since the input is fully server-controlled)
