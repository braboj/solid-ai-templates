# Stack — Static Site Tutorial
[DEPENDS ON: templates/stack/static-site-astro.md, templates/base/workflow/issues.md, templates/base/workflow/scope.md]

Extends the Astro static site stack with conventions for multi-chapter
tutorial sites. Covers content structure, chapter format, diagram
pipeline, CI/CD, and licensing.

---

## Content layer
[OVERRIDE: static-site-content]

Canonical tutorial content lives in `chapters/` as SSG-agnostic
Markdown. The Astro site imports from this directory — never edit
content inside `astro-site/` directly.

```
chapters/
  01-introduction.md
  02-topic-a.md
  ...
  NN-glossary.md
```

- Number-prefixed filenames control chapter order
- Frontmatter MUST include `title`, `section`, `order`
- Content is SSG-agnostic — no Astro-specific syntax in chapters

---

## Chapter structure

Every chapter MUST follow this structure in order:

1. Frontmatter (`title`, `section`, `order`)
2. `## Overview` — what the chapter covers and why
3. Content sections with `##` and `###` headings
4. `## Exercises` — hands-on tasks with verification steps
5. `## Quiz` — multiple-choice questions with answers at the bottom

Reference chapters (playbook, appendix, glossary) MAY omit Exercises
and Quiz sections.

---

## Quiz formatting

- Each option on a bullet line: `- A) ...`, `- B) ...`
- Vary the correct answer positions — never all the same letter
- Answers section at the bottom: `1. C — explanation`

---

## Writing style
[EXTEND: base-docs]

- **American English** spelling (analyze, not analyse)
- Concise, direct sentences — no filler, no preamble
- Explain technical terms inline for beginners
- No `---` separators between subsections — headings provide separation
- No inline Practice sections — all practice goes in Exercises
- No emojis unless explicitly requested

---

## Cross-references

- Reference other chapters by file: `[Topic A](02-topic-a.md)`
- Reference sections within a chapter by heading anchor:
  `[Section Name](#section-name)`
- The Astro build rewrites chapter cross-references automatically
  via a remark plugin (see
  [Single-source pattern](static-site-astro.md#single-source-content-pattern))

---

## Assets
[OVERRIDE: static-site-assets]

```
assets/
  images/              # PNG exports used in chapters
  drawio/              # draw.io source files (editable)
  archive/             # Superseded images (kept for reference)
  banners/             # Banner images
```

- Source files: `assets/drawio/<name>.drawio`
- Exported PNGs: `assets/images/<name>.png`
- Reference from chapters: `![Alt text](../assets/images/name.png)`
- Superseded images move to `assets/archive/` — not deleted
- `.bkp` files (draw.io temp) MUST be in `.gitignore`

---

## Project structure
[OVERRIDE: static-site-architecture]

```
chapters/              # Canonical tutorial content (SSG-agnostic)
assets/
  images/              # PNG exports
  drawio/              # draw.io source files
  archive/             # Superseded images
astro-site/            # Astro static site
  src/
    content/           # Content collection (imports from chapters/)
    components/        # Astro components
    layouts/           # Page layouts
    pages/             # Route definitions
    styles/            # Global CSS
    data/              # Site configuration (site.json)
docs/                  # Project docs
  decisions/           # ADRs
  solid-ai-templates/  # Submodule — quality conventions
  dev-journal.md       # Session log
  ONBOARDING.md        # Contributor setup
  PLAYBOOK.md          # Operational reference
```

---

## Navigation

- Hamburger menu for mobile (breakpoint ≤768px)
- All chapters visible when menu is open
- Tab bar for desktop navigation
- `rel="noopener noreferrer"` on all `target="_blank"` links

---

## CI/CD
[EXTEND: base-git]

Two workflows:

**`build.yml`** — triggers on pull requests to `main`
- Checkout, setup Node (pinned to match `engines` in package.json),
  npm ci (with cache), build, link check

**`deploy.yml`** — triggers on push to `main`
- Same build steps as above, plus upload artifact and deploy to
  GitHub Pages

- Use `actions/setup-node` built-in cache (keyed on
  `package-lock.json`)
- Use lychee for link checking against built `dist/` output —
  MUST use `--root-dir dist` to resolve root-relative paths
- Pin Node version to exact version matching `engines` in
  `package.json`

---

## Release process
[EXTEND: base-git]

Follow `templates/base/core/git.md` release process:
1. `git checkout -b chore/release-vX.Y.Z`
2. `git commit --allow-empty -m "chore: release vX.Y.Z"`
3. Push, open PR, merge
4. `git checkout main && git pull`
5. `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`

Tags use semver: `v1.0.0` (lowercase v, three segments). Release
tags MUST be annotated (`-a`) so `git describe` reports them.

---

## Issue templates

Use 5 typed templates from `templates/base/workflow/issues.md`:
- Epic, Task, Bug, Incident, Spike
- Placed in `.github/ISSUE_TEMPLATE/`
- No title prefix — labels identify the type

---

## Licensing

- Tutorial content: CC BY-NC-SA 4.0
- Allows copying and adapting with attribution
- Prohibits commercial use without permission
- Derivatives must use the same license

---

## Scope guard
[EXTEND: base-scope]

- One chapter per session is the default scope for content work
- Diagram, exercise, and quiz changes within that chapter are in scope
- Restructuring other chapters or adding infrastructure is out of scope
  unless explicitly requested

---

## Commands
```
npm run dev      # develop — hot reload at localhost:4321/<base>/
npm run build    # compile — production build to dist/
npm run preview  # verify — preview the production build locally
```
