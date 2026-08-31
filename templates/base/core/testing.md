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
- A test MUST NOT enumerate, signal, or terminate a process it did not
  start, and MUST NOT mutate host state outside the working directory —
  the process table, system services, the registry, or the user's
  running applications. Where the code under test reaches the host,
  the suite MUST stub that boundary rather than exercise it, even when
  the test's own subject is already faked: a fake at one seam does not
  neutralise a real call at another. This is a distinct class from
  in-process leakage, and more severe — the failure is damage to the
  developer's machine, not a flaky test, and a suite doing it can pass
  every assertion while leaving only a line on stderr. Code that
  reaches the host SHOULD take that reach as an injectable dependency
- A failing test MUST trigger an investigation before any other action —
  never suppress or skip a failing test without a documented reason
- Tests are code and MUST be treated as such — they MAY contain bugs; when
  a test behaves unexpectedly, the test logic MUST be verified before
  concluding the code under test is at fault
- Integration tests MUST use real dependencies for the boundary under test —
  not hand-written mocks

---

## A negative assertion is only as strong as its coverage

[ID: testing-negative-assertion-coverage]

A test that asserts nothing was found passes identically when nothing was
examined — it cannot tell a clean repository from an unread one. A citation
gate asserting `found == []` passed on every run while twelve citations sat
in commented configuration its roots never reached, because the roots were
Python-only. Coverage is the part no failing test reports.

- A test asserting that a set of violations is empty MUST also assert that
  its inputs were reached. Compare the discovered file list against what
  the roots are meant to cover, so a root dropped, mistyped or filtered out
  fails loudly rather than passing quietly
- That coverage assertion MUST be a real comparison, not a count printed
  for a reader to notice. A number in the output is evidence only if
  something fails on it
- A scan MUST report every occurrence, not the first per line or per file.
  A first-match scan undercounts, and the count is what a reader uses to
  decide whether the work is done — a gate that undercounts the remaining
  work fails at the one number it exists to produce
- An assertion that a property holds across a set MUST fail when the set
  shrinks unexpectedly. "Every committed export was taken at the documented
  scale" also passes when a source is deleted, because there is then less
  to measure
- The coverage assertion SHOULD be its own test with its own message,
  rather than a guard clause inside the property test. "The enumeration is
  broken" and "a file violates the rule" are different failures wanting
  different fixes, and a single test reports whichever fires as the same
  red
- Where the corpus has a known floor, assert the floor rather than mere
  non-emptiness. A set that should hold nineteen members and holds one
  passes a non-empty check while measuring almost nothing
- The floor is a threshold, so it is sized from a measurement and carries
  its derivation beside the constant. It cannot be derived from the corpus
  it guards, because comparing a set against its own size is vacuous. An
  append-only corpus — decision records, changelog entries, migrations,
  anything immutable once merged — takes its measured count, which only
  ever rises; a churning one — tracked files, modules, routes — takes a
  stated margin below it, so an ordinary deletion cannot fail an unrelated
  rule
- The margin is for legitimate shrinkage, not for the failure the floor
  catches. Every way an enumeration breaks returns nothing at all rather
  than a fraction, so any floor above zero catches all of them and the
  margin costs no detection. That is what makes a generous margin cheap
  and a missing derivation expensive
- Expect the enumeration to break in ways the assertion cannot see. A
  pattern anchored at the start of a line matches nothing where the lines
  are indented, as commands inside a block are; an enumeration that reads
  the index rather than the working tree cannot see a file that is not
  staged yet. In both the assertion is correct and proves nothing
- Where a project wants this enforced rather than reviewed, the pattern is
  the meta-test in `testing-ast-contract` — assert over the enumeration
  itself, not only over its findings
- That control MUST blind the single call the family reads its corpus
  through — a tracked-file listing, a database cursor, an API client —
  rather than each member's own enumeration. One patch point covers a
  member added later, and needs no knowledge of what each member named its
  reader
- The control MUST derive its members from that call rather than listing
  them. A hand-maintained roster of the checks under control carries the
  blind spot the checks carry: a member missing from the roster is never
  controlled, and the roster reports success while covering less than it
  claims, which is the failure this rule exists to prevent. Selecting on
  the shared call also fails a member written later without a coverage
  assertion, which a roster cannot do
- The control's own discovery count is a floor like any other and takes
  the same sizing. Its corpus is the members themselves, which churn, so
  it takes a stated margin rather than the measured count: retiring a
  member is an ordinary deletion, and a control sized to the exact count
  fails it with a message about a corpus reader when nothing about the
  reader has changed. This is the floor most likely to be written without
  a margin, because the author is counting the members they have just
  finished writing — and everywhere else in this section "the floor" names
  what a member reads, so nothing has taught the reader to apply the rule
  here
- The control SHOULD ship as a test rather than a one-off run, so that
  member fails on the pull request that adds it rather than at the next
  audit

---

## A remedy naming another check is a claim about that check
[ID: testing-remedy-cross-reference]

`testing-negative-assertion-coverage` covers a check that reads nothing.
Neither it nor a rule about a weakened test covers a check whose failure
message names a sibling as the thing that diagnoses the underlying cause.
Narrowing the sibling falsifies the message, and nothing reports it: the
claim lives in a string a passing run never prints, the change is to one
module and the falsified claim sits in another, so there is no failing
test, no diff on the file that broke, and no signal to a reviewer.

A line-ending gate reported that a file the version control system
classifies as binary escapes normalisation, and its remedy said a sibling
character gate names the offending byte and its line. That was true and
load-bearing -- one NUL was what made a document store as binary while the
line-ending gate read clean. Relaxing the character gate to stop holding
documentation to ASCII is well founded, and the obvious implementation
drops documentation from it entirely, which leaves the remedy pointing at
a check that no longer reads the file class the remedy is about. Both
suites stay green.

- A check MAY name another check in its failure message as what diagnoses
  the cause. That reference is a claim about the other check, and it
  decays like any other cross-reference
- Before narrowing what a check examines, search the suite for the
  module's own name. A hit in another check's remedy text is a claim to
  re-verify or re-word in the same change
- The search is the whole control. The claim lives in a string that a
  passing run never prints and a failing run prints only for the other
  check, so no assertion covers it and no diff shows it
- Report what the search examined, not only what it found. An empty result
  is a real answer where the module is spelled as the tree spells it, and
  a mistyped name produces the same empty result from a search that read
  nothing

```bash
# The module whose scope is narrowing, spelled as the tree spells it.
module="<module-under-change>"

scanned=$(git ls-files 'tests/*.py')
echo "test modules scanned: $(echo "$scanned" | grep -c .)"
naming=$(echo "$scanned" | grep -v "/${module}[.]" | xargs grep -l "$module")
echo "modules naming ${module}: $(echo "$naming" | grep -c .)"
echo "$naming"
```

Pass condition: the command reports how many test modules it scanned and
which of them name the module under change, then lists them. Every hit is
read against the change, since a remedy naming the module is a claim to
re-verify or re-word alongside it. A scanned count of zero is the failure
-- the search reached nothing -- while a naming count of zero against a
non-zero scan is a real answer.


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

## Assert against the external definition, not your own output
[ID: testing-external-definition]

A suite can be blind by construction rather than by omission. Where the
code under test and the code asserting on it share an assumption, every
assertion agrees and the assumption itself is never tested. Adding tests
does not reach it and coverage does not report it — the lines are
covered, and they are covered by a witness that cannot disagree.

- A round trip through your own encoder and decoder proves that they
  agree, not that either is correct. A serializer and its parser are
  usually written together, so a defect in one is mirrored in the other.
  Three of exactly this shape shipped in one library and survived 258
  passing tests: a checksum written high byte first and read high byte
  first where the format sends it low byte first; a length-prefixed
  frame written whole and read as whatever one socket read returned,
  which coincide on a local link and diverge across a router; an
  identifier written as a constant and never compared on read
- Where a format is defined outside the codebase — a wire protocol, a
  file format, a checksum, a serialization spec — at least one case MUST
  assert against a fixed vector published by that specification. A suite
  that never leaves the library measures self-consistency
- Assert what an object does, not what the runtime says it is. A check
  phrased against a runtime implementation detail — a type identity, the
  particular exception class raised for a protocol violation, an
  attribute the runtime happens to expose — tests the runtime, and can
  pass for the very defect it was written to catch on a platform or
  version other than the author's
- `threading.Lock` is a type on Windows and a builtin function on Linux,
  so `not isinstance(x, type)` is true of the missing-parentheses defect
  on one platform and false on the other; entering the unconstructed
  class raises `AttributeError` on Python 3.10 and `TypeError` on 3.13.
  Both assertions were written to catch that defect and both varied
- Exercise the object instead — acquire it, release it, enter it. Where
  the test asserts a misuse fails, assert that it fails, not how

---

## Inject a platform-dependent fault, do not wait for the platform
[ID: testing-platform-fault-injection]

A test that only fails on one platform is a test that does not run for
whoever is not on it. The dangerous case is not a failing CI job — that
is loud — but an investigation concluded on the author's platform and
recorded as settled, in a commit message or an issue, where nothing
later rereads it.

- Where behaviour depends on the operating system, the filesystem, the
  locale, or the interpreter version, the suite MUST reproduce the fault
  with a double rather than wait for the platform to supply it. Raise
  the error the other platform raises, from a stub at the same seam the
  real call sits on
- A component cleared by a test on one platform is cleared on that
  platform only. Where that clearing is written down — a commit message,
  an issue comment, a review — it MUST name the platform the evidence
  came from, so the next reader can see what was not covered rather than
  inheriting a conclusion
- A suspected component that turns out to be innocent is the case to
  distrust. A confirmed defect is retested until it goes away; an
  exonerated one is closed, and nothing revisits it
- Worked example: a socket teardown helper was suspected during a
  connection-reset fix, tested on Windows where `shutdown()` on a reset
  socket is silent, found not to raise, and recorded as cleared in both
  the commit message and the issue. On Linux the same call raises
  `ENOTCONN`. The helper was the remaining half of the bug, and the
  closed issue kept reproducing on the only platform CI runs — through
  three pushes, because the local suite was green each time

---

## Allocate a per-test resource outside the class hierarchy
[ID: testing-unique-resource-allocation]

A test base class that hands out a unique resource from a class
attribute stops handing out unique values the moment it is subclassed.

```python
class ServerFixture(unittest.TestCase):
    port_counter = 20200

    def setUp(self):
        # Reads the inherited value and writes the result as a NEW
        # attribute on the subclass, so the sequence restarts per
        # subclass rather than continuing.
        type(self).port_counter += 1
        self.port = type(self).port_counter
```

Every subclass starts from the same base number and issues the same
sequence, so three test classes all bind 20201, 20202, 20203 — while the
code reads as though there is one counter.

- A unique per-test resource — a port, a temporary directory, a database
  name, a queue — MUST come from a module-level counter or a fixture,
  never from a counter on a class other tests inherit
- The collision is invisible where the resource is released promptly and
  fatal where it lingers, so it is a platform difference like any other
  (`testing-platform-fault-injection`). In the reporting project it
  produced a ten-minute CI hang rather than a visible failure: the second
  bind failed inside a worker thread and the caller was waiting on it
  with no timeout
- Check that no test allocates through the subclass, reporting the files
  reached as well as the hits:

  ```bash
  grep -rcE '^[^#]*type[(]self[)][.][A-Za-z_]* *[+]=' tests/ | wc -l
  grep -rnE '^[^#]*type[(]self[)][.][A-Za-z_]* *[+]=' tests/
  ```

  The first line counts the files inspected and MUST be non-zero; the
  second MUST print nothing. A zero count means the path is wrong, not
  that the suite is clean
- The `^[^#]*` prefix keeps the scan on lines where the pattern is used
  rather than discussed, so a comment naming it is not a hit. A trailing
  comment on a real allocation still is one, because the `#` falls after
  the match. Without the prefix the check lands on compliance: a project
  that never had the defect has nothing to say about it and passes, while
  one that hit it, fixed it, and left the reasoning at the fixture is the
  one reported. A rule that bans a pattern has to exclude the regions
  where the pattern is the subject rather than the instrument

---

## Guard the no-leaked-worker invariant with an autouse fixture
[ID: testing-worker-leak-guard]

`base-testing-general` requires a test to leave no host state behind. A
suite that violates it looks identical to a clean one, because the damage
lands after the test that caused it: the offending test passes, something
unrelated later fails, or the run ends with a traceback beside the summary
that reads as a failure and is not one.

Review does not reach it either. The reviewer sees a fixture that calls a
stop method and sleeps, which looks like teardown, and whether the sleep
is long enough is a property of the thing being stopped rather than of the
diff.

- Where a suite starts a background worker — a thread, a subprocess, a
  server — an autouse fixture MUST assert at the end of every test that
  none survives it
- The assertion MUST run per test, not once at session end. A session-end
  check reports that something leaked, not which test leaked it, and
  naming the culprit is the whole value
- The message MUST name the leak and what to do about it. The cause is
  nearly always a fixture that slept instead of joining, and the sleep is
  usually shorter than the wait it stands in for
- Leave it on permanently. It enumerates live workers and waits for
  nothing, so a clean run pays one list comprehension per test

```python
SERVER_THREAD_NAME = "AppServerSim"


@pytest.fixture(autouse=True)
def no_server_thread_outlives_the_test():
    yield

    survivors = [
        t for t in threading.enumerate() if t.name == SERVER_THREAD_NAME
    ]

    if survivors:
        pytest.fail(
            f"{len(survivors)} {SERVER_THREAD_NAME} thread(s) still running "
            "after the test. Call stop() and then join() it with a timeout "
            "in tearDown -- a sleep is a guess, not a wait."
        )
```

---

## Where a fix changes where a value comes from, assert provenance
[ID: testing-assert-provenance]

A defect is sometimes not "the value is wrong" but "the value is not
ours". The code inherits a setting from a platform, a library default, an
ambient config, or a parent process. Today that inherited value happens
to be correct; the defect is that nothing in the code says so, and
nothing would notice when the platform changes.

A TLS client built its context without setting a minimum protocol
version, so its floor came from whichever OpenSSL was linked. The natural
regression test —

```python
assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2
```

— passes on the development machine before and after the fix, because
that OpenSSL already defaults to TLS 1.2. Green, meaningless, and
indistinguishable from a real guard.

- Where a fix's subject is the source of a value rather than the value,
  an assertion on the value does not test the fix. Assert provenance
  instead: inject a source that would yield a different value, and assert
  the code overrides it. In the example, substitute a context whose
  starting floor is TLS 1.0 and assert the library raises it — that fails
  against the unfixed source, which is what the test was for
- Running the new test against the unfixed code is necessary and says
  nothing about what to do when it passes. The instinct is that the fix
  was unnecessary; the correct conclusion is that the assertion is aimed
  at the wrong property
- Substitute at the seam the module under test reads, not at the module
  that defines the type. A standard-library type's own methods may
  resolve their class through a module attribute, so replacing
  `ssl.SSLContext` on the `ssl` module sends the library's own
  `minimum_version` setter back into the double and it recurses.
  Redirecting only the name the module under test reads is the working
  seam
- Distinct from `testing-fix-fires-on-real-data`, where the new code did
  fire and produced no observable difference, and from
  `testing-platform-fault-injection`, whose trigger is a fault that
  cannot be reproduced locally. Here the local value is correct, and that
  is exactly what hides the missing guarantee

---

## Verify a visual change against the render
[ID: testing-verify-the-render]

When a change's intended effect is visual — a style edit, a template, a
chart, a rendered document — re-reading the source proves only that the
source changed. Several things break the link between source and result
silently: a design token resolves to an unexpected value, a more
specific rule wins the cascade, a built or deployed artifact lags its
source until pushed, or a cached copy is served.

- MUST verify by capturing the rendered output and asserting on it —
  render headless, then read the value off the pixels or the resolved
  DOM, not off the stylesheet
- SHOULD capture the before as well as the after. The before confirms
  the problem is real; a page may already satisfy the request, making
  the change a fix for nothing
- When the render still looks wrong, confirm it is the fresh build
  before re-editing. Correct source and a stale deploy is the common
  shape of "it's still broken" reported against already-fixed code

This complements golden-output gating, which pins structure and text but
cannot answer whether something is actually black, centred, or on screen.

---

## A diagnostic view runs through the production entry point
[ID: testing-diagnostic-production-path]

When a diagnostic or debug rendering of a multi-stage pipeline exists —
per-stage dumps, trace overlays, an "explain this output" view — it MUST
be driven from the same entry point as the production path it inspects:
same input resolution, same config or profile selection, same fan-out.

A sibling command with its own setup diverges from production silently.
It keeps running, keeps producing plausible output, and reports on a
computation production never ran — so the bundle can look correct while
production ships a wrong value, and the reverse.

- Wire the diagnostic into the production entry point behind a flag
  (`--debug`, `--explain`), not into a second command
- A parameter the production caller passes and the diagnostic does not is
  the whole defect. Any divergence in what the two resolve is a
  divergence in what they compute
- This is a standing property of a persistent diagnostic view, distinct
  from choosing the production harness over a throwaway probe for a
  one-off question

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
- **Export list vs bindings** — an export list is a hand-written manifest
  of what a module binds, kept beside the bindings and drifting from them
  silently. Python `__all__` holds strings, so an entry can name nothing
  and `from pkg import ThatName` fails for a name the package advertises;
  a TypeScript barrel has the inverse failure, where a symbol meant to be
  exported is absent and no consumer of the barrel can tell. Assert that
  every entry resolves against the live module, naming the offenders:

  ```python
  missing = sorted(n for n in pkg.__all__ if not hasattr(pkg, n))
  assert missing == [], missing
  ```

  The linter covers only half of it, and not the half that matters: ruff
  `F822` reports an undefined `__all__` entry in a plain module and stays
  silent in `__init__.py`, which is where a package's export list lives —
  it cannot see the names a package binds through its submodules, so it
  declines to guess. Introspecting the imported module can. A language
  that puts the export where the compiler sees it (Rust `pub use`, Go's
  capitalised identifiers) needs no guard, which is the test for whether
  this applies
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

## Prove a whole-tree rewrite preserved meaning with an AST comparison
[ID: testing-ast-equivalence]

The sibling of `testing-characterization-fingerprint`: the fingerprint
proves a *refactor* preserved output, this proves a *rewrite* preserved
meaning. Adopting an auto-formatter across an existing tree rewrites
almost every file, and the reviewer's question is always whether any of
it is a behaviour change. The output fingerprint does not answer it
directly — the output is unchanged only if you already believe the
rewrite was mechanical, which is the thing in question.

Compare syntax trees rather than output. Every mainstream language
exposes them: Python `ast.parse` / `ast.dump`, Go `go/parser` with
`go/ast`, TypeScript through the compiler API, Java `JavaParser`.

```python
import ast
import pathlib
import sys


def fingerprint(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    # State the normalisation, because it is what makes the comparison
    # sound. Collapsing whitespace inside string constants is right for
    # a formatter, which re-indents docstring bodies, and wrong for a
    # refactor that may legitimately change a literal.
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = " ".join(node.value.split())

    return ast.dump(tree)


before, after = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
names = sorted(p.relative_to(after).as_posix() for p in after.rglob("*.py"))
differs = [n for n in names if fingerprint(before / n) != fingerprint(after / n)]

print(f"{len(names)} file(s) compared, {len(differs)} with a changed tree")

for name in differs:
    print(f"  {name}")
```

- The compared count MUST equal the number of files the rewrite touched.
  A short or zero count means the traversal missed the tree, not that the
  rewrite was clean
- Every reported file MUST be inspected by hand and accounted for. That
  list is the whole value: it turns "trust the formatter" into an
  exhaustive statement of what changed semantically. One adoption
  rewrote 53 of 56 files and reported a single differing tree, which had
  lost a redundant `u""` prefix the language ignores
- The comparison is only sound if the normalisation is stated. Name it
  beside the run, so a reader can see which differences were declared
  invisible before the result was read
- Where the adoption is recorded as a decision, the record cites this
  comparison rather than an assurance that the tool is safe

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

---

## Derive the test tier from the directory, default to fast
[ID: testing-tier-by-directory]

The taxonomy classifies test types and the regression table names smoke
/ quick / full triggers, but nothing ties them together: how a tier is
DERIVED and how the default run excludes the heavy tier. Hand-marking
every test file drifts from where the test actually lives.

- **Derive the tier from the directory** with a single collection hook
  (pytest `pytest_collection_modifyitems`, or the runner's equivalent):
  `tests/*` → unit, `tests/integration/` → integration, `tests/e2e/` →
  e2e. The tier follows from location, so a marker cannot drift from
  where the test sits
- **Make the default run the fast tier** (unit + integration) and gate
  the heavy tier (container, browser) behind an opt-in marker PLUS an
  optional-dependency extra, so the common path stays fast and the
  expensive dependencies are not installed for it
