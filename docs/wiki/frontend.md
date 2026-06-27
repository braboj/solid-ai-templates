# Frontend UI — Wiki

[ID: frontend-wiki]
[DEPENDS ON: frontend/quality.md, frontend/ux.md]

Wiki notes on reusable frontend application structures. Each
entry describes a problem, solution structure, when to use it,
and examples.

See `frontend/quality.md` for design patterns and state management.
See `frontend/ux.md` for accessibility and responsive design.

---

## 1. Error boundary

[ID: frontend-wiki-error-boundary]

**Problem:** A runtime error in one component crashes the entire
application. Users see a blank screen with no way to recover.

**Solution:** Wrap component subtrees in an error boundary that
catches rendering errors and displays a fallback UI. The rest of
the application continues to function.

```
App
├→ ErrorBoundary → Header (continues working)
├→ ErrorBoundary → MainContent (crashes → shows fallback)
└→ ErrorBoundary → Footer (continues working)
```

**When to use:**

- Around independent sections of the page (sidebar, main, widgets)
- Around third-party components that may throw
- NOT around the entire app — that gives you one giant fallback

**Example (React):**

```tsx
class ErrorBoundary extends React.Component<Props, State> {
  state = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    logError(error, info);
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}
```

**Rules:**

- Error boundaries catch rendering errors only — not event
  handlers, async code, or server-side rendering
- Log the error before showing the fallback — silent failures
  are worse than crashes
- Provide a recovery action in the fallback (retry button,
  link to home)
- Place boundaries at natural isolation points — not around
  every component

---

## 2. Skeleton loading

[ID: frontend-wiki-skeleton]

**Problem:** Content loads asynchronously. The page shows a blank
area or a spinner until data arrives. Layout shifts when content
appears — CLS increases, perceived performance drops.

**Solution:** Render placeholder shapes that match the layout of
the incoming content. When data arrives, replace skeletons with
real content. No layout shift because the skeleton reserves the
exact space.

```
Loading:  [████████]  [████]  [██████████]
Loaded:   John Smith  Admin   john@example.com
```

**When to use:**

- Content loaded asynchronously (API calls, lazy loading)
- Above-the-fold content where a spinner feels slow
- Lists and tables with known structure but unknown data

**Rules:**

- Skeleton shape MUST match the real content layout — same height,
  same width, same spacing
- Use CSS animation (pulse or wave) to indicate loading — static
  grey boxes look broken
- Do not show skeletons for content that loads in under 200ms —
  the flash is worse than a brief wait
- Prefer skeletons over spinners for structured content; use
  spinners only for actions (form submit, navigation)

---

## 3. Optimistic update

[ID: frontend-wiki-optimistic]

**Problem:** After a user action (like, save, delete), the UI
waits for the server response before updating. The delay makes
the interface feel sluggish — especially on slow networks.

**Solution:** Apply the expected result immediately in the UI.
Send the request in the background. If the request fails, roll
back to the previous state and notify the user.

```
User clicks "Like" → UI shows liked (instant)
                   → API call in background
                   → Success: done
                   → Failure: roll back, show error
```

**When to use:**

- Actions with a high success rate (> 99%)
- Actions where the expected outcome is predictable
- Low-stakes operations (likes, bookmarks, toggles)
- NOT for payments, destructive operations, or actions with
  unpredictable outcomes

**Rules:**

- Always implement the rollback path — optimistic without rollback
  is a data integrity bug
- Show a non-intrusive error on failure — do not silently revert
- Store the previous state before applying the update
- Do not use optimistic updates for operations that affect other
  users' data in real time

---

## 4. Infinite scroll with virtualization

[ID: frontend-wiki-virtual-scroll]

**Problem:** Rendering thousands of DOM elements for a long list
freezes the browser. Pagination breaks the browsing flow. Loading
all items at once wastes bandwidth.

**Solution:** Render only the items visible in the viewport plus
a small buffer. As the user scrolls, swap items in and out of the
DOM. Fetch more data when approaching the end of the loaded set.

```
[buffer]
[visible viewport — 20 items rendered]
[buffer]
... 10,000 items total, only ~30 in DOM
```

**When to use:**

- Lists with more than 100 items
- Items have a consistent or estimable height
- The user needs to browse, not search or filter (for search, use
  server-side filtering with pagination)

**Rules:**

- Measure or estimate item height — variable heights require a
  measuring step or estimated height with correction
- Keep a buffer of 5-10 items above and below the viewport to
  prevent flashing during fast scrolling
- Show a loading indicator at the bottom when fetching more data
- Provide a "back to top" button for long lists
- Use established libraries: `react-window`, `@tanstack/virtual`,
  `vue-virtual-scroller`

---

## 5. Debounced search

[ID: frontend-wiki-debounced-search]

**Problem:** A search input fires an API call on every keystroke.
Typing "camera" sends 6 requests, 5 of which are immediately
obsolete. The server is overloaded, responses arrive out of order,
and the UI flickers.

**Solution:** Debounce the input — wait until the user stops
typing for a short delay before sending the request. Cancel any
in-flight request when a new one starts.

```
Keystroke: c-a-m-e-r-a
Requests:  ............→ "camera" (one request after 300ms pause)
```

**When to use:**

- Search inputs that trigger API calls
- Filter controls that cause expensive recomputation
- Auto-save features

**Rules:**

- Debounce delay: 200-400ms — shorter feels responsive, longer
  reduces server load
- Cancel previous requests (AbortController) — stale responses
  must not overwrite fresh results
- Show a loading indicator after the debounce fires, not on
  keystroke — avoids flicker
- Provide immediate local filtering when possible, defer API
  calls for server-side search

---

## 6. Form validation pattern

[ID: frontend-wiki-form-validation]

**Problem:** Validation logic is scattered across event handlers,
submit functions, and inline checks. Error messages appear
inconsistently — some on blur, some on submit, some never.

**Solution:** Centralize validation rules per field. Validate on
blur (field level) and on submit (form level). Display errors
consistently next to the field they belong to.

```
Field blur  → validate field → show/clear field error
Form submit → validate all   → show all errors, focus first
```

**When to use:**

- Any form with more than 2 fields
- Forms with cross-field validation (password confirmation,
  date ranges)

**Rules:**

- Validate on blur for immediate feedback — do not wait for submit
- Validate on submit as a safety net — blur validation alone
  misses untouched fields
- Show errors below the field, not in a summary at the top —
  users should not scroll to find what is wrong
- Focus the first invalid field on submit
- Use a validation library for complex forms: Zod, Yup,
  React Hook Form, VeeValidate
- Never rely on client-side validation alone — always validate
  on the server

---

## 7. Responsive layout switch

[ID: frontend-wiki-responsive-switch]

**Problem:** A data table works on desktop but is unusable on
mobile. Hiding columns loses information. Horizontal scrolling
is awkward. The same data needs two fundamentally different
presentations.

**Solution:** Render both layouts. Use CSS to show the appropriate
one based on viewport width. No JavaScript media queries needed —
the HTML is server-rendered, CSS handles visibility.

```
Desktop (> 640px): table with sortable columns
Mobile  (≤ 640px): card stack with key fields
```

**When to use:**

- Data tables with 5+ columns
- Content that requires fundamentally different layouts per
  breakpoint — not just reflowing
- Static sites where JavaScript-based responsive switching adds
  unnecessary complexity

**Rules:**

- Render both layouts in the HTML — CSS controls visibility
- Mobile-first: design the card layout first, add the table as
  a desktop enhancement
- Both layouts MUST show the same data — do not hide information
  on mobile
- Use a single data source — do not duplicate data fetching or
  state between layouts
- Test both layouts — queries like `getAllByText` verify content
  exists in both views

---

## 8. URL state synchronization

[ID: frontend-wiki-url-state]

**Problem:** Users apply filters, sort a table, and select a tab.
When they share the URL or refresh the page, all state is lost.
The page resets to its default view.

**Solution:** Synchronize UI state with URL search parameters.
Read initial state from the URL on mount. Update the URL when
state changes. The URL becomes a shareable, bookmarkable
representation of the current view.

```
User applies filters → URL updates: ?mount=X&sort=price&dir=asc
User shares URL      → recipient sees the same filtered view
User refreshes       → state restored from URL
```

**When to use:**

- Filter, sort, and pagination controls
- Tab or view selection
- Any state the user would want to share or bookmark

**Rules:**

- Use `replaceState` for filter changes — do not pollute browser
  history with every keystroke
- Use `pushState` for navigation-like changes (tab switch, page)
- Parse URL params on mount — the URL is the source of truth,
  not component state
- Validate URL params — malformed or injected values must fall
  back to defaults, not crash
- Keep param names short but readable: `sort`, `dir`, `page`,
  not `sortColumn`, `sortDirection`, `currentPage`
