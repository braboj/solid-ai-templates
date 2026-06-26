# Stack — Hugo Static Site
[DEPENDS ON: templates/frontend/static-site.md]

Extends the static site stack with Hugo-specific rules. Covers content
organisation, archetypes, shortcodes, themes, and deployment.

---

## Stack
[OVERRIDE: static-site-stack]

- Framework: Hugo (latest stable)
- Templating: Go templates (`html/template`)
- Content: Markdown + front matter (YAML or TOML)
- Styling: [plain CSS / Tailwind (via PostCSS) / CSS Modules]
- JS: [none / Alpine.js / minimal vanilla JS] — avoid heavy frameworks
- Deployed via GitHub Actions on push to `main`

---

## Project structure
[OVERRIDE: static-site-architecture]

```
content/               # all Markdown content — mirrors URL structure
  _index.md            # home page content
  [section]/
    _index.md          # section list page
    [post].md          # single content page
archetypes/            # templates for `hugo new` command
  default.md
data/                  # structured data files (JSON, YAML, TOML)
layouts/               # Go template overrides
  _default/
    baseof.html        # base layout
    single.html        # single page layout
    list.html          # list page layout
  partials/            # reusable template fragments
  shortcodes/          # custom shortcodes
static/                # files served as-is (images, fonts, favicon)
assets/                # files processed by Hugo Pipes (CSS, JS)
themes/                # submodule or local theme (if using one)
hugo.toml              # main configuration (prefer TOML)
README.md
CLAUDE.md
```

---

## Content structure
[OVERRIDE: static-site-content]

- All content in `content/` as Markdown files with YAML/TOML front matter
- Front matter MUST include: `title`, `date`, `draft` — add `description`
  and `tags` for SEO-relevant content
- `draft: true` content is never published — remove or set `false` before merge
- Section structure mirrors the URL: `content/blog/my-post.md` → `/blog/my-post/`
- Use `_index.md` for section list pages and the home page
- Data that is referenced by templates (e.g. nav links, team members) goes
  in `data/` as JSON or YAML — never hardcoded in templates

---

## Templates and partials
[ID: hugo-templates]

- All template logic in `layouts/` — never modify a theme's files directly;
  override by mirroring the path in the project's `layouts/` directory
- Keep `baseof.html` minimal — define blocks (`{{ block "main" . }}`) and
  fill them in `single.html` and `list.html`
- Extract repeated template fragments into `layouts/partials/` —
  call with `{{ partial "name.html" . }}`
- Shortcodes for reusable content patterns used in Markdown —
  one file per shortcode in `layouts/shortcodes/`
- No business logic in templates — complex data transformations belong
  in `data/` files or Hugo's `config/` params, not in template conditionals

---

## Assets
[OVERRIDE: static-site-assets]

- Source assets (CSS, JS) in `assets/` — processed by Hugo Pipes
- Static files (images, fonts, favicon) in `static/` — copied as-is
- Reference static files as `/filename.ext` — never with a relative path
- Use `resources.Get` + `resources.ExecuteAsTemplate` for CSS processing;
  use `js.Build` for JS bundling if needed

---

## Code conventions
[OVERRIDE: static-site-code]

- Configuration in `hugo.toml` (TOML preferred over YAML for Hugo)
- Environment-specific config in `config/_default/`, `config/production/`
- No inline CSS or JS in templates — keep presentation in `assets/`
- `{{ safeHTML }}` and `{{ safeURL }}` only when the content is genuinely
  trusted and controlled — never on user-generated content

---

## Performance
[EXTEND: frontend-quality]

- Use Hugo's built-in image processing (`images.Resize`, `images.Process`)
  for responsive images — never commit unoptimised originals as final assets
- Minify HTML, CSS, and JS in production: `hugo --minify`
- Avoid loading external resources (fonts, scripts) from third-party CDNs
  without a `preconnect` hint

---

## SEO
[EXTEND: static-site-seo]

- `robots.txt` generated from `layouts/robots.txt` template
- Open Graph and Twitter Card meta tags in `layouts/partials/head.html`
- Canonical URLs via `{{ .Permalink }}` — Hugo handles these automatically
  when `canonifyURLs = true` is set in config

---

## Testing
[ID: hugo-testing]

A Hugo site has no unit-test suite — "testing" means verifying the
built output:

- Build MUST succeed with zero errors and zero warnings:
  `hugo --gc --minify` (treat `WARN` as a failure in CI)
- Internal and external links MUST resolve — run `lychee` over
  `public/` after the build
- Lighthouse CI SHOULD meet budgets: accessibility ≥ 90, performance /
  SEO / best practices ≥ 90
- Validate generated HTML (e.g. `html-validate`) when the theme is
  hand-authored

---

## Git conventions
[EXTEND: base-git]

- Do not commit `public/` — the build output is generated on deploy
- Do not commit `resources/_gen/` — Hugo regenerates these from source
- If using a theme as a Git submodule, commit `.gitmodules` and the
  submodule pointer; document the `git submodule update --init` step in README

---

## Commands
```
hugo server           # develop — hot reload at localhost:1313
hugo server -D        # develop — include draft content
hugo                  # production build → public/
hugo --minify         # production build with minification
hugo new [section]/[name].md  # create content from archetype
```