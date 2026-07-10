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
  `templates/base/workflow/quality-gates.md` for the coverage policy (80% for
  new projects,
  warn-only for legacy)
- Coverage MUST NOT regress between releases
- MUST be runnable from CI without human intervention
- Names are not part of any external report or traceability system — they
  SHOULD be chosen freely, provided the name alone communicates the unit under
  test, the input condition, and the expected outcome; each stack template
  defines its own naming convention
- When the unit operates on a structured external artifact (a config file,
  a code-generated file, a captured fixture), run it against real
  production data once during development before declaring the unit suite
  sufficient. Fabricated-input tests cover the cases the author imagined;
  production data exposes the structural holes nobody fabricated. The run
  does not replace unit tests — it surfaces gaps to close with a dedicated
  regression test per invariant

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
- SHOULD run browser-driven UI journeys against an in-process app server
  (WSGI/ASGI/Node) on an ephemeral port, kept separate from the container
  e2e tier — so a CSP, JS, or MIME regression stays catchable locally even
  when the container runtime is unavailable; the two tiers are
  independently runnable

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

---

## Shared-path fixes verify every call site
[ID: testing-shared-path-breadth]

A fix that changes a shared code path may surface latent bugs at other
call sites that were silent before. Verification MUST exercise every
call site sharing the changed code, not only the case from the bug
report.

- Run the project's ground-truth comparison (golden tests, reference
  data, recorded fixtures, snapshot suite) on every entity exercising
  the path — "expected unchanged" is the bug case, so verify it rather
  than assume it
- Enumerate every downstream consumer of the changed surface — each
  tool or report that derives a committed artifact from it — and re-run
  it, so a stale artifact does not misread as the fix not working.
  Document the consumer list alongside the surface so the sweep stays
  cheap to repeat
- A silent prior bug at a sibling call site surfaces only in the
  broader benchmark — the breadth of verification bounds the fix's
  value

---

## Verify the fix fires on real data
[ID: testing-fix-fires-on-real-data]

When a fix targets a specific in-the-wild case, run the actual pipeline
on that input and compare its output to the committed or expected values.
Indirect green signals each lie independently: unit tests pass (the
synthetic input took the new branch), the full suite passes (no
regression), and staleness checks pass (no committed artifact changed) —
while the new code never fires on the real case because the real input
lacks the shape the fix assumed. The test that matters is
`run-pipeline <bug-input> | diff - <expected>`: it confirms the code both
reached the bug site AND took the new branch.

---

## Identical metrics across distinct inputs are a smoking gun
[ID: testing-identical-metrics]

When diagnostic output (test verdicts, IoU or coverage scores, lint
counts) reports identical values across two distinct inputs, treat it as
a shared root cause first and coincidence second — it usually means both
inputs route to the same asset (a path-resolution bug), hit the same
fallback or sentinel branch, or map to the same config row. This is more
actionable than "both inputs fail": matching values point at one bug, not
two.

- Diff the two inputs' upstream resolution (asset path, profile binding,
  config row) before diffing their downstream outputs
- File as one issue, not two — a fix on the shared code resolves both
- If the inputs are genuinely independent with no shared upstream, the
  collision itself is the bug worth flagging

---

## Enforce the public-API contract with an AST meta-test
[ID: testing-ast-contract]

A blanket annotation linter rule (e.g. ruff `ANN`) forces `Any` and
noise onto private helpers that legitimately take un-stubbed third-party
objects, so teams either over-lint or let the "every public function
carries full type hints and a documented docstring" contract drift.
Split the rule: the linter owns format and complexity; a test owns the
*presence* of annotations and docstring sections on the public surface
only.

- Parse each module with the language's AST (Python `ast`, TypeScript
  via the compiler API, Go `go/ast`) and filter the public defs:
  top-level non-underscore functions plus public methods of public
  classes
- Assert every parameter (except `self`/`cls`) and the return is
  annotated, that param'd defs carry an `Args:` section, and that
  value-returning defs carry `Returns:`. Emit failures as
  `file:line name(param)` so each is self-documenting
- Roll out behind an allowlist inside the test: sweep module by module
  and flip the global gate last, so no PR is a big-bang unreviewable
  sweep
- The same AST/token pass cheaply enforces adjacent rules a linter has
  no rule for — a comment trailing code on the right, a ticket/PR/ADR
  number embedded in a comment — reusing one traversal

---

## Drift-guard meta-tests pin a duplicated fact to its source
[ID: testing-drift-guard]

Single-source-of-truth is the goal, but some facts unavoidably live in
two places: a hand-authored contract file and the code that implements
it, a documented limit and the constant that enforces it, a version
string reported at runtime and the package metadata. Without a guard the
copies drift silently — the exact failure single-source is meant to
prevent. Any fact represented twice gets a test that fails when the
copies diverge, introspecting the live artifact rather than hardcoding
the expected value.

- **Constant vs contract** — assert the documented limit in the spec
  file equals the code constant that enforces it
- **Route coverage** — introspect the router (Flask `url_map`, Express
  router stack, Go mux) and assert every live route appears in the
  contract document, so a new or renamed endpoint left undocumented
  fails CI with no human diff review
- **Version parity** — assert the version reported at runtime equals the
  installed package metadata, and that the contract's own version field
  is present
- Prefer introspection so the test cannot itself drift, and keep the
  guard one-directional: assert the derived copy matches the source of
  truth, not the reverse. Complements the AST contract test
  (`testing-ast-contract`) in the "enforce what the linter can't" family

---

## Prove a behaviour-preserving refactor with a fingerprint
[ID: testing-characterization-fingerprint]

When a refactor changes structure but is meant to leave output
unchanged, "I didn't mean to change it" is not proof — a reordered dict,
a 1-ULP float shift, or a changed RNG draw order silently perturbs a
large output that unit tests check only in the small. Extend the
ground-truth comparison (`testing-shared-path-breadth`) to the whole
output:

- **Fingerprint the full output before, reproduce and diff after** —
  reduce the entire output (not a rounded or sampled view) to one exact
  fingerprint, a hash of the full-precision bytes; capture it before the
  refactor and regenerate after. Identical output is provably behaviour-
  preserving; any diff is a real change to investigate
- **Seed everything nondeterministic** (RNG, clock, iteration order) so
  the fingerprint is stable and a diff means a regression, not noise
- **Keep the fingerprint disposable** — it is a private scaffold for the
  duration of the refactor, not a fixture. A committed platform-dependent
  hash goes CI-flaky across machines and toolchains; commit invariant
  property tests instead. The fingerprint proves the refactor, the
  invariants guard the future

---

## Serve the real app in-process on an ephemeral port
[ID: testing-in-process-server]

Between the framework's in-process test client (bypasses the real
WSGI/ASGI/HTTP server, its response headers, and static-file MIME
resolution) and a full container (slow, needs a runtime) sits a
lightweight middle option: start the real application on an
OS-assigned port in a daemon thread and drive it over real HTTP. This
is the in-process tier the E2E policy names.

- **Bind to port 0** so the OS assigns a free port; derive the base URL
  from the assigned port and tear the server down in a `finally`. A
  fixed port collides across parallel tests and repeated runs; port 0
  never does
- **It exercises the real server stack** — routing, serialization,
  response headers, static-file content types — that an in-process test
  client silently bypasses
- **One recipe, two consumers** — a driver / screenshot script and a
  browser-based UI test fixture share the same "serve the real app
  ephemerally" helper, so UI tests need no container
- Every server exposes this primitive: Python
  `werkzeug.serving.make_server(..., 0, ...)`, Node `server.listen(0)`,
  Go `httptest.Server` (the standard library blessing the pattern).
  Use the in-process thread when you need only the app; reserve a
  container when you need the built image or sidecar services

---

## Container e2e: runtime-agnostic and health-gated
[ID: testing-container-e2e]

When an e2e test needs the real built image, hardcoding Docker and a
fixed `sleep` breaks on rootless Podman, in CI without Docker, and when
the container is slow to start. Drive the image through the Docker API
instead of the Docker CLI:

- **Runtime-agnostic via a Docker-compatible API** — drive containers
  through a library that speaks the Docker API (Testcontainers and
  equivalents) so the SAME test runs on Docker or rootless Podman by
  pointing at whichever socket is present (`DOCKER_HOST`); no test
  change per runtime
- **Poll until healthy, never sleep** — gate readiness with a poll loop
  against the container's health endpoint plus a deadline, so a slow
  start waits and a dead start fails fast
- **Import-guard the optional dependency** (`pytest.importorskip` or
  equivalent) so the module still collects, and skips cleanly, in jobs
  that do not install the heavy e2e extra
- **Disable the resource reaper on rootless runtimes** — Ryuk and its
  kin assume a privileged Docker; a meta-assertion MAY also verify the
  image runs as a non-root user

This is programmatic single-image e2e from the test suite; local
multi-service dev composition lives in `containers.md`.
