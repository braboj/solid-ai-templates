# Base — Testing

[ID: base-testing]

## Patterns

- Use factory, AAA, builder, parameterized, fixtures, mock boundary,
  snapshot, and contract testing patterns where appropriate

## Taxonomy

Test types are classified by the **boundary crossed during execution** — not by
who runs them, what tools are used, or what assets drive the test content.

| Type            | Boundary crossed                     | Primary focus                                   |
| --------------- | ------------------------------------ | ----------------------------------------------- |
| **Unit**        | None — single component in isolation | Correctness of individual functions and classes |
| **Integration** | Process or component boundary        | Behaviour and interaction across components     |
| **System**      | System boundary                      | End-to-end behaviour from a user perspective    |
| **Regression**  | Any — reuses existing tests          | Protection against unintended change            |
| **Exploratory** | Any — unscripted                     | Discovery of unexpected behaviour               |

---

## Unit tests

Unit tests verify the correctness of individual functions and classes in
isolation. Dependencies MUST be replaced with mocks or stubs. The primary
driver is TDD — tests are written alongside or before the code.

- MUST cover all happy paths defined by functional requirements
- MUST achieve 90% coverage of new code before merging
- SHOULD cover negative scenarios and edge cases
- The total codebase SHOULD maintain 80% unit test coverage — see
  `templates/base/workflow/quality-gates.md` for the coverage policy (80% for new projects,
  warn-only for legacy)
- Coverage MUST NOT regress between releases
- MUST be runnable from CI without human intervention
- Names are not part of any external report or traceability system — they
  SHOULD be chosen freely, provided the name alone communicates the unit under
  test, the input condition, and the expected outcome; each stack template
  defines its own naming convention

---

## Integration tests

Integration tests verify behaviour and interactions across a process or
component boundary using real dependencies (database, message queue, filesystem,
communication partner). Mocks MUST NOT substitute the dependency being
integrated — they MAY be used for unrelated dependencies outside the scope
of the test.

Configuration MAY be sourced from the product specification when the
integration requires a formally defined input. This does not change the
classification — the boundary crossed determines the type, not the asset
used.

- MUST verify the primary interaction path between the integrated components
- SHOULD cover fault scenarios — dependency unavailable, malformed response,
  timeout, boundary violations
- SHOULD cover cases where a behaviour is only valid under specific conditions
- MUST NOT rely on shared mutable state between test runs
- Names SHOULD follow a structured codification scheme that enables
  filtering, traceability, and maintenance across projects

---

## System tests

System tests verify the complete product against its documented requirements
from a user perspective, crossing the system boundary (interacting with
external systems, users, or interfaces).

- MUST be driven by the product manual or system specification
- MUST cover the primary user scenarios defined in the requirements
- SHOULD cover fault and degraded-mode scenarios at the system level
- MUST be executed in an environment representative of production

### E2E tests (subset of system)

E2E tests are automated system tests that simulate complete user journeys
through the full product stack.

- MUST cover the critical user journeys defined in the product requirements
- SHOULD cover non-happy paths and system-level edge cases
- MAY provide data-agnostic scenarios to reduce environment coupling

### Acceptance tests (subset of system)

Acceptance tests are always executed manually, typically by the QA department
or the customer, to determine whether the product satisfies its acceptance
criteria.

- MUST be executed in the target environment with production-representative
  configuration
- MUST be driven by documented acceptance criteria — not improvised
- Automated tests MAY support acceptance testing but MUST NOT replace manual
  sign-off

---

## Regression tests

Regression tests protect against unintended change by re-executing a defined
subset of existing tests after a modification. They reuse unit, integration,
and system tests — they are not a separate test type.

Regression suites are divided by scope and execution time:

| Variant   | Scope               | Trigger             | Target duration |
| --------- | ------------------- | ------------------- | --------------- |
| **Smoke** | Critical paths only | Every commit        | < 15 minutes    |
| **Quick** | Core functionality  | Every merge request | < 60 minutes    |
| **Full**  | Complete suite      | Release candidate   | Unrestricted    |

- Smoke and Quick regression MUST be fully automated
- Full regression SHOULD be fully automated; manual steps MUST be documented
- A regression failure MUST trigger an investigation:
  1. Review the test logic first — if incorrect, refactor the test
  2. If the test logic is correct, investigate the code under test

---

## Exploratory tests

Exploratory testing is unscripted, experience-driven investigation with no
predefined expected outcome. It is not part of any regression suite.

- MAY be triggered by a discovered bug, a release candidate, or intuition
- Findings that reveal a defect SHOULD result in a new regression test to
  prevent recurrence
- Results SHOULD be documented informally (session notes, bug reports)

---

## Testability

Testability is a first-class design concern, not an afterthought. Code
that is hard to test is hard to test because it is poorly designed —
fixing the design fixes the testability.

### Pure functions over side effects

- Business logic SHOULD be implemented as pure functions — same input,
  same output, no side effects (no I/O, no mutation of external state)
- Side effects (database, API, filesystem, DOM) SHOULD be pushed to
  the boundary — thin adapters that call pure logic
- Pure functions are trivially unit-testable with no mocks, stubs, or
  setup
- A function that mixes logic and side effects is a signal to split
  it: extract the logic into a pure function, keep the side effect
  in a thin wrapper

### Architecture for testability

- Push side effects to the edges:
  `[boundary: I/O] → [pure: logic] → [boundary: I/O]`
- The pure center is unit-testable; the thin boundaries are
  integration-testable
- If a function needs more than two mocks to test, it has too many
  responsibilities — split it

### SOLID enables testability

- **SRP** — one responsibility = one reason to test; multiple
  responsibilities require combinatorial test cases
- **OCP** — new behaviour via extension means existing tests stay
  green
- **LSP** — subtypes that honour contracts can be tested against the
  base type's tests
- **ISP** — small interfaces mean fewer dependencies to mock
- **DIP** — depend on abstractions, inject dependencies; code that
  instantiates its own dependencies cannot be tested in isolation

### Design patterns and composition

- Design patterns enable testability by enforcing separation of
  concerns, loose coupling, and clear contracts
- Prefer composition over inheritance — composed dependencies can be
  injected and swapped in tests; inherited behaviour drags the entire
  class hierarchy into every test

---

## General rules
[ID: base-testing-general]

- Design for testability from the start — do not write code first and
  struggle to test later
- If code is hard to test, treat it as a design problem, not a testing
  problem
- Test behaviour, not implementation details
- Each test MUST be independent — no shared mutable state between tests
- Environment variables and other process-global state are shared
  across the entire test process. A module that mutates the
  environment (or any global) at *import time* leaks the change into
  every test, and import order is not guaranteed. Tests that depend
  on a variable being a specific value — including *unset* — MUST
  set or clear it explicitly per test (e.g. `pytest`'s
  `monkeypatch.setenv` / `monkeypatch.delenv`, equivalents in other
  frameworks), never rely on the ambient process state. A test that
  passes or fails depending on run order is an isolation bug, not
  flakiness
- A failing test MUST trigger an investigation before any other action —
  never suppress or skip a failing test without a documented reason
- Tests are code and MUST be treated as such — they MAY contain bugs; when
  a test behaves unexpectedly, the test logic MUST be verified before
  concluding the code under test is at fault
- Integration tests MUST use real dependencies for the boundary under test —
  not hand-written mocks

---

## Tests should name what they pin
[ID: testing-name-what-pinned]

A test that asserts a numeric threshold (precision ≥ 0.85, latency
< 100ms, IoU ≥ 0.20) MUST document what about the system the threshold
pins — otherwise an intended improvement that legitimately moves the
number produces a failure indistinguishable from a real regression, and
nobody can tell whether to lower the bar, update the test, or revert.

State, in the docstring or assertion message:

- the relationship under test (the property the threshold gates)
- the conditions it was calibrated under (pipeline state, reference data)
- the expected response if a future improvement legitimately moves it

Flag in review a single-number assertion whose failure message names
only the observed value ("Expected ≥ 0.85, got 0.81") — make it
actionable ("Expected ≥ 0.85 polyline-on-skeleton precision, a
self-consistency check calibrated post-#953; got 0.81 — verify the
skeleton is still the dense per-curve trace the threshold assumed").
This applies to threshold-asserting tests specifically, not every test.

---

## Data validation tests
[ID: base-testing-data-validation]

Per-record validation (no duplicates, required fields present, range
and enum checks) confirms each entry is well-formed but cannot see a
partial migration — orphan keys and missing entries are individually
valid. A cohort-level assertion catches what per-record checks miss.

- **Coverage-by-cohort** — when a bulk migration writes N records keyed
  by a derived slug, assert that the set of written keys equals the set
  of expected slugs derived independently from the source-of-truth.
  Catches orphan entries (key with no consumer) and missing entries
  (consumer with no key); one assertion replaces ad-hoc post-merge
  spot-checks
- The pattern generalizes to any bulk migration where producer and
  consumer derive keys independently from a shared concept
