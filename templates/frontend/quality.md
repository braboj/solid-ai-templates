# Frontend — Quality Attributes

[ID: frontend-quality]
[DEPENDS ON: templates/base/core/quality.md]

## Patterns

- Use error boundary, skeleton loading, optimistic update, virtual
  scroll, debounced search, form validation, responsive switch, and
  URL state sync patterns where appropriate

## Design patterns

Prefer these patterns for frontend concerns:

- **Container / Presentational** — separate data-fetching and state logic
  (container) from rendering (presentational); presentational components
  receive only props, have no side effects, and are easy to test in isolation
- **Custom Hook** — extract reusable stateful logic into a named hook
  (`use[Name]`); hooks are the frontend equivalent of a service or strategy
- **Compound Component** — expose a set of related sub-components that share
  implicit state via context (e.g. `<Tabs>`, `<Tab>`, `<TabPanel>`);
  prefer over deeply nested prop drilling
- **Render Props / Slot** — pass render logic as a prop or slot to invert
  control over what is rendered; use sparingly — prefer custom hooks where
  possible
- **Observer** — subscribe to external state changes (store, event bus,
  WebSocket) via a single subscription point; unsubscribe on component unmount
- **Facade** — wrap third-party libraries (analytics, maps, payment SDKs)
  behind a thin project-owned interface; never scatter SDK calls across
  components
- **Optimistic Update** — apply the expected result of a mutation immediately
  in the UI and roll back on failure; document the rollback path

Avoid:

- **Mediator / Event Bus** between components — use shared state or lifting
  state up instead; an event bus between components creates invisible coupling

## State management

Choose the right tool for the scope of the state — do not use a global store
for state that is local to a component or a server cache for state that is
never fetched from a server.

| State type          | Scope                | When to use                                       |
| ------------------- | -------------------- | ------------------------------------------------- |
| **Local UI state**  | Single component     | Form inputs, toggles, counters                    |
| **Shared UI state** | Multiple components  | Auth session, sidebar state, active filters       |
| **Server state**    | Cached from API      | Lists, detail views, paginated results            |
| **Form state**      | Form lifecycle       | Validation, field arrays, multi-step flows        |
| **URL state**       | URL search params    | Bookmarkable filters, pagination, selected tab    |

Rules:

- Never duplicate server state in a global store — use a dedicated server
  cache; the store holds only client-owned state
- Never put derived state in the store — compute it from existing state
- Prefer URL state for anything the user should be able to bookmark or share
- Keep global store slices small and focused — one slice per domain concern,
  not one slice for everything

## Linting and formatting

- A linter MUST be configured for all JS/TS code
- Linter and formatter SHOULD run on save in the IDE — never rely on CI
  alone to catch style issues
- No warnings or errors MUST appear in the browser console or test output
  before a PR is merged — start every review on a clean slate
- Lint error count SHOULD go down over time — never increase it

## CSS

- No inline styles except for dynamic/computed values
- No hardcoded colour or spacing values — always use CSS custom properties
  from `:root` or design tokens
- Consistent naming convention (e.g. BEM-like `.component-element`)
- Maximum line length: 80 characters (exempt: prose strings, third-party URLs)

## Performance

- Preload critical above-the-fold assets
- Keep client-side JS minimal — every dependency adds to bundle size
- Avoid unnecessary dependencies
- Defer non-critical scripts
- Monitor Core Web Vitals (LCP, CLS, INP) — treat regressions as bugs

## SEO & analytics (if applicable)

- `robots.txt`, Open Graph, and Twitter Card meta tags required for
  server-rendered and static pages
- Canonical URLs required for publicly indexed pages
- MUST pick a trailing slash convention (with or without) and enforce it
  across all internal links, canonical URLs, and sitemap entries — redirect
  chains waste crawl budget, split link equity, and can prevent indexing
- Verify the chosen convention matches the hosting platform's behavior
- Privacy-friendly analytics only — no consent banner required
- No third-party tracking scripts without explicit user consent
- If `og:image` is present, `twitter:image` MUST also be present —
  Twitter/X does not reliably fall back to `og:image`. Include
  `og:image:width`/`og:image:height` (recommended 1200×630) to avoid
  render delays on social platforms
- H1 keywords SHOULD appear in the page body — search and answer engines
  use heading/body coherence as a relevance signal; H1 SHOULD be unique
  per page and reflect its content
- Provide a complete favicon set: an SVG favicon
  (`<link rel="icon" type="image/svg+xml">`) and a 180×180
  `apple-touch-icon` for iOS home-screen bookmarks
- Answer engines retrieve passages, not whole pages — lead each section
  with a direct answer and keep paragraphs self-contained
- Measure answer-engine (AEO) visibility as citation frequency across a
  fixed prompt set over time, not as a single rank — generative output is
  non-deterministic

## Structured data (if applicable)

- Schema `@type` MUST match the page's actual role — do not use
  `Product` + `Offer` on informational pages that do not sell anything
- Fields MUST NOT imply capabilities the site lacks (e.g. `availability`
  implies commerce, `priceValidUntil` implies a store)
- Review schema choice when site role differs from template examples —
  e-commerce examples applied to editorial sites produce misleading markup
- `FAQPage` markup SHOULD NOT be expected to render a Google rich result
  (gov/health only since 2023) — it still aids machine parsing for answer
  engines
