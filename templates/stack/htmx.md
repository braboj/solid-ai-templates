# Stack — HTMX
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/core/config.md, templates/base/security/security.md, templates/backend/templating.md]

Extends server-side templating with HTMX hypermedia conventions. Covers swap
strategies, triggers, out-of-band updates, server-sent events, Alpine.js
integration, and testing. Language-agnostic — compose with any backend stack
(python-django, python-flask, go-echo, node-express, etc.).

---

## Stack
[ID: htmx-stack]

- UI library: HTMX 2.x
- Sprinkle JS (optional): Alpine.js 3.x
- Template engine: [Jinja2 / Django templates / Go html/template / Handlebars]
- Backend: [any — see DEPENDS ON]

---

## Project structure
[ID: htmx-structure]

HTMX composes with a backend stack that owns the overall layout. HTMX
adds a fragment-oriented template tree:

- `templates/` — full-page templates that extend a base layout
- `templates/partials/` — HTML fragments returned by HTMX endpoints,
  one file per swappable component
- Name partials by the component they render, not the route that
  returns them: `partials/cart_items.html`, not `partials/get_cart.html`
- Keep each fragment renderable both standalone (HTMX swap) and
  included in a full page (initial load) — no logic that assumes one
  context

---

## Core principles
[ID: htmx-principles]

- The server is the source of truth — HTML is the API response, not JSON
- Every interaction returns HTML fragments, not data; the client never
  constructs UI from JSON
- Avoid JavaScript for anything the server can handle — HTMX attributes
  in HTML are the primary interaction mechanism
- Progressive enhancement: pages MUST be functional without JavaScript;
  HTMX adds interactivity on top

---

## Attributes and triggers
[ID: htmx-attributes]

- Use `hx-get`, `hx-post`, `hx-put`, `hx-delete` for HTTP methods —
  match the semantic intent of the operation
- Use `hx-trigger` to control when requests fire:
  - `click` — default for buttons
  - `change` — for inputs and selects
  - `submit` — for forms
  - `every 5s` — for polling; prefer SSE for real-time updates over polling
- Use `hx-target` to specify where the response is inserted —
  always be explicit; avoid relying on default parent-swap behaviour
- Use `hx-swap` to control the insertion strategy:
  - `innerHTML` — replace content inside the target (default)
  - `outerHTML` — replace the target element itself
  - `beforeend` — append to a list
  - `delete` — remove the target after a successful response

---

## Partial responses
[ID: htmx-partials]

- HTMX requests MUST receive partial HTML — never return a full page layout
  in response to an HTMX request
- Detect HTMX requests server-side via the `HX-Request: true` header —
  return the partial template; fall back to the full page for non-HTMX requests
- Return `HTTP 204 No Content` for operations that produce no UI update
  (e.g. a delete with no visible replacement)
- Return `HTTP 422 Unprocessable Entity` for validation errors — re-render
  the form partial with inline error messages

---

## Out-of-band updates
[ID: htmx-oob]

- Use `hx-swap-oob="true"` to update multiple page regions in a single
  response — e.g. update a counter in the nav while also updating the list
- Keep OOB updates to a minimum per response — more than two or three
  OOB targets in one response is a signal that the interaction is too complex
- Name OOB target IDs clearly and consistently: `#notification-count`,
  `#cart-total`

---

## Server-sent events
[ID: htmx-sse]

- Use SSE (`hx-ext="sse"`) for real-time server push — prefer SSE over
  polling for live data (notifications, progress, feed updates)
- SSE connections are long-lived — ensure the server supports concurrent
  open connections without exhausting worker threads (async handlers or
  dedicated SSE workers)
- Always handle SSE reconnection on the client — HTMX's SSE extension
  does this automatically; do not disable it
- Close SSE connections explicitly when the user navigates away

---

## Alpine.js integration
[ID: htmx-alpine]

- Use Alpine.js for client-side state that does not require a server round-trip:
  toggles, accordions, tabs, dropdowns, modal visibility
- Do not use Alpine.js to manage state that the server should own —
  form data, user records, application state
- Keep Alpine components small — if an `x-data` object exceeds five
  properties, consider whether the interaction belongs server-side
- HTMX and Alpine.js are complementary — HTMX handles server interactions,
  Alpine handles local UI state; do not use them for the same concern

---

## Navigation and history
[ID: htmx-navigation]

- Use `hx-push-url="true"` on navigations that change the logical page —
  ensures the browser back button works and the URL is shareable
- Do NOT push URL for in-place updates that are sub-page (modals, inline
  edits, partial refreshes)
- Use `hx-boost="true"` on `<a>` tags and forms to progressively enhance
  full-page links into HTMX requests

---

## Loading states
[ID: htmx-loading]

- Use `hx-indicator` to show a loading indicator during requests —
  point to a spinner or skeleton element
- Disable the triggering element during a request with `hx-disabled-elt="this"`
  to prevent duplicate submissions
- Always give the user feedback within 200ms of an interaction —
  show a spinner if the response takes longer

---

## Testing
[EXTEND: backend-templating-testing]

- Test each HTMX endpoint returns a partial (not a full page) when the
  `HX-Request` header is present
- Test the fallback full-page response when `HX-Request` is absent
- Test OOB swap targets are present and correctly populated in the response
- Test that form validation errors return `422` with inline error markup
- End-to-end tests with Playwright — assert DOM changes after HTMX swaps
  complete, not immediately after click

---

## Commands
```
# No build step required — HTMX is a single script tag or npm package
# Include via CDN in development:
# <script src="https://unpkg.com/htmx.org@2"></script>
# Bundle via your backend's static asset pipeline in production
```