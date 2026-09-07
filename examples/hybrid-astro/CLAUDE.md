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

When the user signals end of session ("wrap up", "let's finish", "end
session", "close out", or similar), print the full checklist below and
execute each item sequentially. Mark each item done (with result) before
moving to the next. Do not batch, skip, or summarize — visible sequential
execution prevents missed steps.

1. **Commits and push** — all changes committed and pushed (via PR if
   branch-protected)
2. **Close issues** — reconcile the open-issue list against the work
   shipped this session, from the tracker rather than memory, and close
   what is done (verify auto-close worked)
3. **Epic checklists** — update epic checklists if relevant
4. **ADRs** — apply the decision threshold in
   `docs/solid-ai-templates/templates/base/core/docs.md`: a record is
   owed when the decision changes what a user of the thing observes
   without reading the repository's internals. Prose style, tool choice,
   release procedure, naming and file layout need none; one coherent
   architectural choice may span PRs.
5. **CLAUDE.md** — for each new convention/rule, apply the doc-placement
   decision tree in `ai-workflow.md` (Doc placement decision tree
   section): evaluate code → ADR → README → PLAYBOOK → CLAUDE.md →
   memory in order. CLAUDE.md is the home ONLY if the agent MUST apply
   the rule on every turn.

   CLAUDE.md contains rules only — not changelogs, package architecture,
   per-feature progress, or session logs. Keep rules concise without
   removing necessary qualifiers; paragraph length does not require an
   ADR.
6. **README.md** — for each new command, dependency, or structural
   change, is it reflected? Name the section.
7. **ONBOARDING.md** — ensure `docs/ONBOARDING.md` exists and covers
   each new tool, prerequisite, or setup step. Create it if missing;
   name the section. A missing doc is work to do here, not a gap to
   report.
8. **PLAYBOOK.md** — ensure `docs/PLAYBOOK.md` exists and covers each
   new command, script, or workflow added. Create it if missing; name
   the section. A missing doc is work to do here, not a gap to report.
9. **Submodules** — review updates needed for the current task or a
   material security risk. A newer template tag alone creates no update
   obligation; follow the adoption boundary above before changing a pin.
10. **Template feedback** — propose upstream work for a demonstrated
    shared defect or recurring need. Check existing issues first. A
    reusable-looking preference alone requires no issue, ADR, or
    `Upstream:` bookkeeping; contribute when the user has authorized
    that work.
11. **Build and checks** — run `npm run check` and `npm run build` and
    confirm both pass.
12. **Flag gaps** — if any item cannot be completed this session, report
    it as pending (never as done) before closing — including deferred
    cross-repo work, such as an upstream contribution that was flagged
    but not yet landed. Reserve "pending" for work that is genuinely
    blocked — it needs a decision, a credential, or the user. Work the
    agent could do but has not done is not pending; do it.
13. **Dev journal** — add a session entry to `docs/dev-journal.md`
    (date, tool, key changes, PRs merged, issues closed/created). This
    item sits after flagging gaps because it is the only one whose
    output is a record of the others, and flagging a gap resolves into a
    change whenever the fix is small enough to apply on the spot — which
    is when a wrap-up should apply one. Written earlier, its
    merged-pull-request, issue and upstream lines are incomplete by
    construction, and an entry's account is fixed once written, so the
    correction costs a second entry for one session
    - Where the checklist runs more than once in a session — a release
      wrap-up, then a close-out — only the last pass writes the entry.
      An earlier pass records that the session owes one. The entry is
      owed by the session and discharged once, at the end
14. **Summary** — summarize what was done and what is next
