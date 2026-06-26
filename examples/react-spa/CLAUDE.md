# AdminFlow

Analytics dashboard for monitoring SaaS subscription metrics and
customer health.

- Owner: Growth engineering
- Repo: github.com/acme/adminflow
- Deployment: Vercel — production on merge to `main`, preview per PR
- Model: inline

> Generation inputs (per ADR-016 — examples are agent-generated
> outputs of the documented pipeline):
>
> - Stack source: `stack/spa-react.md`
> - Resolved chain: `generated/stack-react-spa.md` (base + frontend +
>   spa-react)
> - Output format: `base/core/agents.md` (inline model)
> - Project brief: AdminFlow — Growth engineering — TypeScript /
>   React 18 / Vite 5 / TanStack Router + Query v5 / Zustand /
>   Tailwind CSS v3 — Vitest + RTL, Playwright, msw — pnpm — Vercel

This file is self-contained: all rules are inlined, no external
templates need to be read.

## 1. Project

### 1.1 Overview

- Model: inline
- Language: TypeScript (strict mode)
- Framework: React 18
- Bundler: Vite 5
- Routing: TanStack Router
- Server state: TanStack Query v5
- Client state: Zustand
- Styling: Tailwind CSS v3
- HTTP client: TanStack Query + native fetch
- Test runner: Vitest + React Testing Library
- E2E: Playwright
- Network mocking: msw (Mock Service Worker)
- Linter: ESLint + `eslint-plugin-sonarjs` + `eslint-plugin-jsx-a11y`
- Formatter: Prettier (owns all formatting decisions)
- Package manager: pnpm
- Deployment: Vercel — automatic on merge to `main`

### 1.2 Project structure

```
src/
  components/
    Charts/
      LineChart.tsx
      LineChart.test.tsx
    Filters/
      DateRangePicker.tsx
      DateRangePicker.test.tsx
    UI/                 # shared design-system components
      Button.tsx
      Badge.tsx
      Table.tsx
  pages/
    Dashboard.tsx       # /
    Customers.tsx       # /customers
    Subscriptions.tsx   # /subscriptions
    Settings.tsx        # /settings
  hooks/
    useMetrics.ts
    useCustomers.ts
    useAuth.ts
  services/
    api.ts              # base fetch wrapper, auth headers, errors
    metrics.ts
    customers.ts
  store/
    authStore.ts        # Zustand — current user, session
    uiStore.ts          # Zustand — sidebar state, active filters
  types/
    api.ts              # API response types
    domain.ts           # Customer, Subscription, Metric shapes
  utils/
    formatters.ts       # currency, date, percentage formatters
    validators.ts
  index.css             # base resets, CSS custom properties
  App.tsx
  main.tsx
e2e/
  dashboard.spec.ts
  customers.spec.ts
tsconfig.json
vite.config.ts
tailwind.config.ts
package.json
README.md
CLAUDE.md
```

- One directory per feature domain under `components/`
- `src/services/` holds all API calls — no business logic in components
- All editable visual values in `tailwind.config.ts` — never hardcoded

### 1.3 Commands

```bash
pnpm dev            # develop — hot reload at localhost:5173
pnpm build          # production build
pnpm preview        # preview production build locally
pnpm test           # run unit tests (watch mode)
pnpm test:run       # run unit tests once (CI)
pnpm e2e            # run Playwright E2E tests
pnpm lint           # ESLint check
tsc --noEmit        # type check without emitting
```

## 2. Code conventions

### 2.1 Git

- Branch: `main` (protected) — never commit directly
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`,
  `docs/<scope>`
- Commits: `<type>(<scope>): <summary>` — types: feat, fix, chore,
  docs, refactor, style, test; subject under 80 characters,
  imperative mood
- PRs are small and focused — one concern per PR; require one approval
  and passing CI (lint, type check, tests) before merge
- Repeat the closing keyword before each issue number:
  `Closes #a, closes #b` — a bare `#b` stays open
- Never force-push a branch, including with `--force-with-lease`; when
  behind `main`, merge `main` in or use `gh pr update-branch`
- After a PR is merged, delete the branch and pull `main` before new
  work
- Do not commit `node_modules/`, `dist/`, `.env`, `.env.local`
- Lock file (`pnpm-lock.yaml`) is committed — never delete it
- Every repository MUST have a `.gitignore` and a committed lockfile
- Run `pnpm test:run && tsc --noEmit` before every commit

### 2.2 TypeScript

- `strict: true` in `tsconfig.json` — no exceptions
- Follow `@typescript-eslint/recommended`
- No `any` — use `unknown` and narrow, or define a proper type
- Explicit return types on all non-trivial functions
- `interface` for object shapes; `type` for unions and aliases
- Use discriminated unions (a literal `type`/`kind` field) for type
  families — safer than class hierarchies
- No enums — use `as const` objects or string literal unions
- Import types with `import type { ... }` to keep the runtime bundle
  clean
- Booleans prefix with `is`, `has`, or `can` (`isActive`,
  `hasPermission`)
- `eslint-plugin-sonarjs` MUST be in the ESLint config; cognitive
  complexity <= 15 per function
- Prettier owns all formatting — no style discussion in review
- Source files UTF-8, ASCII content only, LF line endings

### 2.3 Components

- One component per file — filename matches component name
  (PascalCase)
- Functional components only — no class components
- Props typed with an explicit `interface` or `type` in the same file
- No prop drilling beyond two levels — use a Zustand store, context,
  or TanStack Query
- Separate container (data + state) from presentational (props only)
  components — presentational components have no side effects
- Extract reusable stateful logic into custom hooks
  (`use[Name].ts` in `src/hooks/`)
- Keep components under ~150 lines — split if larger
- No direct DOM manipulation — all state flows through React

### 2.4 State management

| State type | Tool                     | When to use                     |
| ---------- | ------------------------ | ------------------------------- |
| Local UI   | `useState`, `useReducer` | Form inputs, toggles, counters  |
| Shared UI  | Zustand                  | Auth session, sidebar, filters  |
| Server     | TanStack Query           | Lists, detail views, paginated  |
| URL        | TanStack Router params   | Bookmarkable filters, paging    |

- Server state (API data) lives in TanStack Query — `useQuery`,
  `useMutation`; never duplicate it in Zustand
- Client/global state (auth, UI) lives in Zustand slices in
  `src/store/` — one slice per domain concern
- Never put derived state in the store — compute it from existing
  state
- Prefer URL state for anything the user should bookmark or share

### 2.5 API integration

- All API calls in `src/services/` — never inline `fetch` in
  components
- `src/services/api.ts` is the only place that sets auth headers and
  handles 401 responses (redirect to login)
- Return typed response objects — no untyped `any` at API boundaries
- Validate external responses at the boundary (Zod or equivalent) —
  allowlist valid shapes, reject everything else
- Handle loading, error, and empty states explicitly in every
  data-dependent view
- Tokens stored in memory (Zustand `authStore`) — never in
  `localStorage`; prefer `httpOnly` cookies for refresh tokens
- Encode dynamic data on output — never `dangerouslySetInnerHTML`
  with user-supplied content
- Never hardcode secrets, API keys, or tokens in source — use `.env`,
  commit `.env.example` with placeholders only

### 2.6 Styling

- Tailwind utility classes only — no custom CSS files except
  `src/index.css` for base resets and CSS custom properties
- No inline styles except for dynamic computed values (e.g. chart
  widths)
- No hardcoded colour or spacing values outside `tailwind.config.ts`
- Mobile-first: base styles for mobile, `md:` / `lg:` for larger
  breakpoints
- Breakpoints: small mobile <=480px, mobile <=768px, tablet <=1024px

## 3. Quality

### 3.1 Testing

- React Testing Library for component tests — test behaviour, not
  implementation
- Prefer accessible queries: `getByRole`, `getByLabelText`,
  `getByText` over `getByTestId`
- Mock API calls at the network boundary with `msw` — not inside
  components
- Vitest for unit tests on utils, hooks, and services
- Test factory defaults for optional fields MUST be `undefined`
  (omitted), not convenient values like `false` or `0`
- Component test naming uses Given/When/Then:
  `given an unauthenticated user, when they visit the dashboard,
  then they are redirected to login`
- E2E (Playwright) MUST cover: login, dashboard load, customer
  search, date filter
- New code MUST reach 90% coverage; total coverage MUST NOT regress
  and SHOULD stay at or above 80%
- A failing test triggers an investigation before any other action —
  never skip or suppress without a documented reason
- Run before every commit: `pnpm test:run && tsc --noEmit`

### 3.2 Accessibility

Target WCAG 2.1 AA. Automated tools catch ~30-40% of issues; the
rest require manual testing.

- All interactive elements keyboard-accessible and operable
- Semantic HTML — `<button>` not `<div onClick>`, `<nav>` for
  navigation; any `onClick` element MUST contain a real `<button>`
- Every form input has an associated `<label>` or `aria-label`
- Icon-only or ambiguous links MUST have a descriptive `aria-label`
- Use `:focus-visible` for focus indicators; all links and nav links
  MUST show a visible focus outline
- No content that relies on colour alone to convey meaning
- Colour contrast >= 4.5:1 for normal text, >= 3:1 for large text
- Charts include a `<title>` and an accessible text fallback for
  screen readers
- Modals trap focus, restore it on close, and close on Escape
- Boolean table columns sort descending (true first) on first click

Automated checks (run in CI):

- `jest-axe` (or `@axe-core/react`) — zero violations before merge
- Lighthouse accessibility score >= 90 on all key pages
- `eslint-plugin-jsx-a11y` — catches missing `alt`, bad ARIA, and
  missing labels at write time

Manual checks (before shipping new interactive components):

- Keyboard-only navigation — every action reachable, logical focus
  order, no unintended focus traps
- Screen reader walkthrough (NVDA + Chrome) — content and state
  changes announced correctly
- Zoom to 200% — no clipping or horizontal scroll at a 1280px
  viewport

### 3.3 Performance

- Monitor Core Web Vitals (LCP, CLS, INP) — treat regressions as bugs
- Keep client-side JS minimal — every dependency adds to bundle size;
  defer non-critical scripts
- Preload critical above-the-fold assets
- Use skeleton loading and optimistic updates for perceived speed;
  document the rollback path for every optimistic mutation

## 4. Identity

### 4.1 Design

AdminFlow is an internal admin UI built on a small shared
design system in `src/components/UI/`.

- Use the shared design-system components (`Button`, `Badge`,
  `Table`) — never build ad-hoc components that duplicate them
- Design tokens (colours, spacing, typography, radii) come from
  `tailwind.config.ts` — never hardcode visual values
- Component-driven: build UI as a hierarchy of reusable,
  self-contained components; avoid monolithic page views
- New shared components SHOULD ship with a usage example before
  merge
- Least Surprise: if a control looks like a button it MUST behave
  like a button; keep interaction patterns consistent across pages
- Progressive disclosure: surface only what the user needs at each
  step — dashboards default to summary, drill-downs on demand
- No dark patterns — no misleading UI, forced actions, or hidden
  costs

## 5. Review process

### 5.1 Code review

Before merging, review the diff against the base branch in priority
order (highest first):

1. Security — responses validated at the boundary, no
   `dangerouslySetInnerHTML` with user data, tokens in memory not
   `localStorage`, no secrets in source
2. Correctness — server state in TanStack Query (not duplicated in
   Zustand), API calls only in `src/services/`, loading / error /
   empty states handled, no direct DOM manipulation
3. Clarity — names self-documenting, components single-purpose and
   under ~150 lines, cognitive complexity <= 15
4. Conventions — `strict` clean with no `any`, accessible queries in
   tests, Given/When/Then test names, Tailwind tokens not hardcoded
   values, `jsx-a11y` and `sonarjs` clean

Confirm CI is green and the browser console is free of warnings.
Only merge after the review passes.

### 5.2 Structure audit

- Run `pnpm test:run && tsc --noEmit && pnpm lint` before every PR
- Verify `axe` reports zero violations and Lighthouse a11y >= 90 on
  changed pages
- Verify new components live under the correct feature directory and
  reuse `src/components/UI/` rather than duplicating it
- Verify `README.md` documents the env reference and commands, and
  `.env.example` lists every required variable
- Run the audit after: new project, new route or feature domain, a
  new shared component, or before a release

## 6. Session protocol

### 6.1 Start of session

1. Read this `CLAUDE.md` and `README.md` in full before the first
   change
2. Check the current branch — if not `main`, ask why before
   proceeding
3. Check `git status` — if uncommitted changes exist, ship the
   previous session's wrap (branch, commit, push, merge) before any
   new work
4. Clean up stale branches: `git fetch --prune`, then delete local
   branches whose PRs have merged
5. Check the latest Vercel deploy on `main` completed successfully —
   flag if stuck, failed, or pending
6. Confirm the scope with the user before making changes
7. If the task is ambiguous, ask: "What is the specific deliverable
   for this session?"
8. Review open issues related to the agreed scope before writing code

### 6.2 During the session

- Flag explicitly when a task grows beyond the agreed scope — do not
  silently absorb new requests
- Finishing and committing the current work takes priority over
  starting something new
- Run `pnpm test:run && tsc --noEmit` after every change — do not
  accumulate unverified changes
- When a tool (formatter, codemod) touches unrelated files, revert
  the drift before committing and file it separately

### 6.3 End of session

When the user signals end of session ("wrap up", "let's finish",
"end session", "close out", or similar), print the full checklist
below and execute each item sequentially. Mark each item done (with
result) before moving to the next. Do not batch, skip, or summarize
— visible sequential execution prevents missed steps.

1. Commits and push — all changes committed and pushed (via PR if
   branch-protected)
2. Close issues — close completed issues (verify auto-close worked)
3. Epic checklists — update epic checklists if relevant
4. Dev journal — add a session entry to `docs/dev-journal.md` (date,
   tool, key changes, PRs merged, issues closed/created)
5. ADRs — record any architectural decisions in `docs/decisions/`; a
   new directory or content move between documents each needs an ADR
6. CLAUDE.md — for each new convention, decide whether it belongs
   here (a rule the agent MUST apply every turn) or in another doc;
   keep each rule to one line
7. README.md — for each new command, dependency, or env var, confirm
   it is reflected; name the section
8. docs/ONBOARDING.md — for each new tool, prerequisite, or setup
   step, confirm it is documented; name the section
9. docs/PLAYBOOK.md — for each new command, script, or workflow,
   confirm it is documented; name the section
10. Tests and types — run `pnpm test:run && tsc --noEmit && pnpm
    lint` and confirm all pass
11. Flag gaps — if any item cannot be completed this session, report
    it as pending (never as done) before closing
12. Summary — summarize what was done and what is next
