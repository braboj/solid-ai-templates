# Testing — Wiki

[ID: testing-wiki]
[DEPENDS ON: base/testing.md]

Wiki notes on reusable structures for test code. Each entry
describes a problem, solution structure, when to use it, and
examples.

See `base/testing.md` for test types, coverage targets, and naming.
See `base/quality.md` for testability as a design concern.

---

## 1. Test factory

[ID: testing-wiki-factory]

**Problem:** Tests create domain objects inline with verbose
literal syntax. When a field is added to the type, every test
that constructs that object breaks — even tests that don't care
about the new field.

**Solution:** A factory function returns a valid default object.
Tests override only the fields they care about.

```
makeLens()                    → valid default lens
makeLens({ maxAperture: 1.4 }) → default lens with one override
```

**When to use:**

- Domain objects have more than 3 required fields
- Multiple test files construct the same type
- The type evolves frequently

**Example (TypeScript):**

```typescript
// src/test/factories.ts
export function makeLens(overrides: Partial<Lens> = {}): Lens {
  return {
    model: "XF 35mm f/1.4",
    mount: "X",
    type: "prime",
    focalLengthMin: 35,
    focalLengthMax: 35,
    maxAperture: 1.4,
    weight: 187,
    price: 750,
    ...overrides,
  };
}
```

**Rules:**

- One factory per domain type — co-locate in a test utilities file
- Defaults MUST produce a valid object — no undefined required fields
- Never use random values in defaults — deterministic factories
  make failures reproducible
- Use factory composition for nested types: `makeOrder({ items: [makeItem()] })`

---

## 2. Arrange-Act-Assert

[ID: testing-wiki-aaa]

**Problem:** Tests mix setup, execution, and verification into an
unstructured block. Readers cannot tell what is being tested or
what the expected outcome is.

**Solution:** Structure every test into three visually separated
sections: arrange (setup), act (execute), assert (verify).

```
Arrange — set up preconditions and inputs
Act     — call the function or trigger the behavior
Assert  — verify the outcome
```

**When to use:**

- Every unit and integration test — this is the default structure

**Example:**

```typescript
it("scores weather-sealed lenses higher for landscape", () => {
  // Arrange
  const sealed = makeLens({ isWeatherSealed: true });
  const unsealed = makeLens({ isWeatherSealed: false });

  // Act
  const sealedScore = scoreLandscape(sealed);
  const unsealedScore = scoreLandscape(unsealed);

  // Assert
  expect(sealedScore).toBeGreaterThan(unsealedScore);
});
```

**Rules:**

- One act per test — if you have two acts, you have two tests
- Arrange may be shared via `beforeEach` — but only when all
  tests in the block share the same setup
- Assert should test one logical concept — multiple `expect`
  calls are fine if they verify the same outcome

---

## 3. Builder pattern for test data

[ID: testing-wiki-builder]

**Problem:** Factory functions work for simple objects but become
unwieldy when the object has many optional fields, nested
structures, or requires sequential configuration steps.

**Solution:** A fluent builder chains method calls to construct
complex test data. The final `.build()` call returns the object.

```
aLens().withAperture(1.4).withMount("X").scored().build()
```

**When to use:**

- Objects require more than 5 configuration steps
- Tests need objects in specific states (scored, published, draft)
- Factory overrides become deeply nested

**Example:**

```typescript
class LensBuilder {
  private data: Partial<Lens> = {};

  withAperture(value: number): this {
    this.data.maxAperture = value;
    return this;
  }

  withMount(mount: string): this {
    this.data.mount = mount;
    return this;
  }

  build(): Lens {
    return makeLens(this.data);
  }
}

export const aLens = () => new LensBuilder();
```

**Rules:**

- Builder wraps the factory — do not duplicate default logic
- Use builders only when factories are insufficient — do not
  over-engineer simple test data
- Name builder entry points as articles: `aUser()`, `anOrder()`

---

## 4. Parameterized tests

[ID: testing-wiki-parameterized]

**Problem:** Multiple tests verify the same logic with different
inputs. Each test is a copy of the others with one value changed.
Adding a new case means duplicating the entire test body.

**Solution:** Define test cases as data. A single test body runs
once per case. The test framework provides the parameterization
mechanism.

**When to use:**

- Three or more tests differ only in input and expected output
- Boundary value testing (min, max, zero, negative)
- Mapping or conversion functions with many valid pairs

**Example (Vitest):**

```typescript
it.each([
  { aperture: 1.4, expected: 2 },
  { aperture: 2.8, expected: 1 },
  { aperture: 5.6, expected: 0 },
])("scores aperture $aperture as $expected", ({ aperture, expected }) => {
  const lens = makeLens({ maxAperture: aperture });
  expect(scoreAperture(lens)).toBe(expected);
});
```

**Example (pytest):**

```python
@pytest.mark.parametrize("aperture,expected", [
    (1.4, 2),
    (2.8, 1),
    (5.6, 0),
])
def test_score_aperture(aperture, expected):
    assert score_aperture(aperture) == expected
```

**Rules:**

- Use descriptive test names that include the varying parameter
- Keep the case table close to the test — do not hide it in a
  separate file unless it exceeds 20 entries
- Each row MUST be independent — no row depends on a previous row

---

## 5. Fixture hierarchy

[ID: testing-wiki-fixtures]

**Problem:** Tests duplicate expensive setup (database seeding,
API mocking, DOM rendering). Extracting setup into `beforeEach`
works within one file but does not share across files.

**Solution:** Define fixtures as composable setup/teardown pairs.
Tests declare which fixtures they need. The framework handles
lifecycle.

```
global fixture (once)
  └→ suite fixture (per file)
      └→ test fixture (per test)
```

**When to use:**

- Shared setup across multiple test files
- Setup has teardown requirements (close connection, reset DOM)
- Setup is expensive and should run once per suite, not per test

**Example (Vitest):**

```typescript
// src/test/setup.ts — global fixture
beforeAll(() => {
  // seed test database or start mock server
});

afterAll(() => {
  // cleanup
});
```

**Example (pytest):**

```python
@pytest.fixture(scope="session")
def db():
    conn = create_test_database()
    yield conn
    conn.close()

@pytest.fixture
def user(db):
    return create_user(db, name="test")
```

**Rules:**

- Use the narrowest scope possible — `per-test` over `per-suite`
  over `global`
- Fixtures MUST clean up after themselves — no test pollution
- Never depend on test execution order — each test must work
  in isolation
- Name fixtures after what they provide, not what they do:
  `user` not `createUser`

---

## 6. Mock boundary

[ID: testing-wiki-mock-boundary]

**Problem:** Tests mock internal implementation details. When the
code is refactored, tests break even though behavior is unchanged.
Heavy mocking obscures what is actually being tested.

**Solution:** Mock only at system boundaries — external services,
databases, file systems, clocks. Test internal logic as pure
functions without mocks.

```
[external boundary: mock] → [internal logic: no mocks] → [external boundary: mock]
```

**When to use:**

- Always — this is the default approach
- Override only when testing integration between internal modules
  that cannot be separated

**Rules:**

- If a function needs more than two mocks, it has too many
  responsibilities — split it
- Prefer fakes (in-memory implementations) over mocks (behavior
  assertions) — fakes test behavior, mocks test calls
- Never mock what you own — if you need to mock an internal
  module, the design needs improvement
- Mock the dependency, not the function under test

---

## 7. Snapshot testing

[ID: testing-wiki-snapshot]

**Problem:** Verifying complex output (rendered HTML, serialized
objects, API responses) requires verbose assertions that are hard
to write and maintain.

**Solution:** Capture the output once as a snapshot file. On
subsequent runs, compare the output against the stored snapshot.
Review snapshot changes in code review like any other diff.

**When to use:**

- Rendered component output (HTML, JSX)
- Serialized data structures with many fields
- Error message formatting
- NOT for business logic — use explicit assertions instead

**Rules:**

- Review snapshot diffs carefully — auto-updating masks bugs
- Keep snapshots small — snapshot a component, not a full page
- Use inline snapshots for short output (under 10 lines)
- Never snapshot non-deterministic output (timestamps, random IDs)
  — stabilize the output first (mock clocks, seed randomness)

---

## 8. Contract testing

[ID: testing-wiki-contract]

**Problem:** Service A depends on Service B's API. Integration
tests that call Service B are slow, flaky, and require both
services to be running. Mocking B's responses risks drift —
the mock may not match B's actual behavior.

**Solution:** Define a contract (schema) for the interaction.
The consumer (A) tests against the contract. The provider (B)
verifies it produces responses matching the contract. Neither
service needs the other running.

```
Consumer tests: "I expect this shape from B"
Provider tests: "I produce this shape for A"
Contract:       shared schema both sides verify against
```

**When to use:**

- Microservices or distributed systems with API dependencies
- Teams that own different services
- APIs that evolve independently

**Rules:**

- Consumer writes the contract — the consumer knows what it needs
- Provider verifies the contract in CI — a breaking change fails
  the provider's build
- Version contracts alongside the services
- Use established tools: Pact, Spring Cloud Contract, or
  OpenAPI-driven testing
