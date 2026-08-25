# Frontend — UX Principles

[ID: frontend-ux]
[DEPENDS ON: templates/base/core/quality.md]

## UX principles

- Mobile-first — design for small screens first, enhance for larger ones
- Progressive disclosure — show only what the user needs at each step
- No dark patterns — no misleading UI, no forced actions, no hidden costs
- Consistency — same interaction patterns throughout the product
- Performance is UX — slow interfaces are bad user experience
- **Least Surprise**: components and interactions should behave as users
  expect; if a pattern looks like a button it must act like a button

## Accessibility — WCAG 2.1 AA

- Target standard: WCAG 2.1 AA
- Minimum text contrast ratio: 4.5:1 (normal text), 3:1 (large text)
- All interactive elements reachable and operable by keyboard
- Any non-focusable element (`<th>`, `<div>`, `<span>`) with `onClick` MUST
  contain a `<button>` — `onClick` alone does not add the element to the tab
  order or provide keyboard activation
- Use `:focus-visible` instead of `:focus` for focus indicators —
  `:focus` shows outlines on mouse clicks (distracting), `:focus-visible`
  shows them only for keyboard navigation
- Focus indicators must be visible at all times during keyboard navigation
- All `<a>` elements and nav links MUST have a visible `:focus-visible`
  outline — links often lack focus styles even when buttons have them
- No content that relies on colour alone to convey meaning
- Images must have descriptive `alt` text; decorative images use `alt=""`
- Semantic HTML: correct landmark elements and heading hierarchy
- `aria-label` on all interactive elements (buttons, icon links, social links)
- All `<a>` elements with icon-only or ambiguous text must have a descriptive
  `aria-label`
- Keyboard navigation: menus must close on Escape and restore focus

## Accessibility testing

Meeting WCAG 2.1 AA requires both automated and manual testing — automated
tools catch ~30–40% of issues; the rest require human judgment.

### Automated (run in CI)

- **axe-core** — integrate via the framework adapter (`@axe-core/react`,
  `@axe-core/vue`, `axe-playwright`, or `jest-axe`); zero violations
  allowed before merge
- **Lighthouse** — accessibility score ≥ 90 on all key pages; run in CI
  via `lighthouse-ci`
- **Linter a11y plugin** — catches missing `alt`, incorrect ARIA roles, and
  missing form labels at write time; use the plugin for your framework
  (`eslint-plugin-jsx-a11y` for React, `eslint-plugin-vuejs-accessibility`
  for Vue; Svelte has built-in a11y warnings)

### Manual (run before shipping new interactive components)

- **Keyboard-only navigation** — tab through the entire feature; every
  action reachable without a mouse; focus order is logical; no focus traps
  except intentional modal dialogs
- **Screen reader** — test with at least one: NVDA + Chrome (Windows),
  VoiceOver + Safari (macOS / iOS), or TalkBack (Android); verify that
  all content and state changes are announced correctly
- **Zoom to 200%** — no content clipped or overlapping at double zoom;
  horizontal scroll must not appear on a 1280px viewport
- **High contrast mode** — verify in Windows High Contrast or forced-colors
  CSS media query; no information lost when colours are overridden

### Criteria for done

A feature is not complete until:

- [ ] `axe-core` reports zero violations in component tests
- [ ] Lighthouse accessibility score ≥ 90
- [ ] Keyboard navigation verified manually
- [ ] Screen reader walkthrough completed for new interactive elements

## Sortable tables

- Boolean columns SHOULD sort descending (true first) on first click —
  users click a boolean column to find items that have a feature, not
  items that lack it; ascending puts `false` first, which looks
  identical to unsorted and appears broken

## Responsive breakpoints

- Tablet: max-width 1024px
- Mobile: max-width 768px
- Small mobile: max-width 480px

## Design system

- Use a design system if one exists for the project — never design ad-hoc
  components that duplicate established patterns
- Design tokens (colours, spacing, typography, radii) MUST come from the
  design system — never hardcode visual values
- Component-driven development: build UI as a hierarchy of reusable,
  self-contained components; avoid monolithic views
- New components SHOULD be documented with usage examples before shipping

## Graded variant bake-off
[ID: frontend-ux-bakeoff]

When several UX approaches are plausible, do not pick by fiat:

1. Build N minimal variants (e.g. three editor designs).
2. Grade each on weighted criteria — at least implementation effort and
   UX quality — by exercising them on a dev server, not on paper.
3. Pick the best score-per-effort; record the runners-up and why they
   lost, so the discarded variants document the design space.

## Browser support

[ID: frontend-ux-browsers]

- Default target: last 2 versions of Chrome, Firefox, Safari, and Edge
- Progressive enhancement: graceful degradation for unsupported features
