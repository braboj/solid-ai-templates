# Backend — Microservices
[ID: backend-microservices]
[DEPENDS ON: templates/backend/api.md, templates/backend/http.md, templates/backend/messaging.md]

Rules for projects explicitly built as a microservices architecture.
Do not apply this template to a monolith or a single-service project.

---

## When to use microservices

- Start with a **modular monolith** — well-separated modules within a single
  deployable unit; extract services only when you have a clear, proven reason
- Valid reasons to extract a service: independent scaling requirement,
  independent deployment cadence, different technology requirement,
  organisational team boundary (Conway's Law)
- Invalid reasons: "it feels cleaner", "microservices are modern",
  premature optimisation — the operational cost is real and front-loaded
- A system of two or three services is not microservices — it is a
  distributed monolith waiting to happen; apply these rules only when
  the architecture is intentionally service-oriented

---

## Service boundaries

- Model service boundaries on **bounded contexts** (Domain-Driven Design) —
  each service owns one cohesive domain concept end-to-end
- A service owns its domain: its data, its logic, its API — no other service
  reaches into its internals
- Services MUST NOT share a database — shared databases create invisible
  coupling and make independent deployment impossible
- Shared libraries between services MUST contain only cross-cutting
  infrastructure (logging, tracing, HTTP client config) — never domain logic
- If two services frequently change together, they are probably one service

---

## Inter-service communication

Choose the communication style based on the interaction type:

| Interaction | Style | Example |
|---|---|---|
| Request needs an immediate response | Synchronous (REST or gRPC) | Auth check, price lookup |
| Caller does not need to wait | Asynchronous (events/messages) | Order placed, user registered |
| Streaming or bidirectional | gRPC streaming | Live feed, file upload |

- Prefer **async messaging** for cross-service workflows — it decouples
  availability and reduces cascade failures
- For synchronous calls, always set a timeout and wrap with a Circuit Breaker
- Never chain more than two synchronous service calls in a single request path
  — each hop multiplies latency and failure probability

---

## Data management

- **Database per service** — each service has its own schema and storage;
  no direct cross-service database access, ever
- Accept **eventual consistency** — distributed data cannot be both consistent
  and highly available at the same time (CAP theorem); design UX and business
  logic around it
- Duplicate read-only data across service boundaries via events rather than
  joining across service databases
- Use the **Outbox pattern** to guarantee that database writes and event
  publishing are atomic

---

## Distributed transactions

- Avoid distributed transactions (two-phase commit) — they are fragile and
  do not compose with async systems
- Use the **Saga pattern** for multi-service workflows that must maintain
  consistency:
  - **Choreography saga**: each service listens for events and reacts —
    simple to implement, harder to trace; suitable for short workflows
  - **Orchestration saga**: a dedicated orchestrator service drives the
    workflow and issues compensating actions on failure — preferred for
    complex or long-running workflows
- Every saga step MUST have a defined **compensating action** (rollback
  equivalent) — document it alongside the forward action

---

## API gateway

- Expose a single entry point to external clients via an API gateway —
  never expose internal service URLs directly
- The gateway handles: routing, auth token validation, rate limiting,
  TLS termination, and request logging
- Do not put business logic in the gateway — it is infrastructure, not a service
- Internal service-to-service calls bypass the gateway — use a service mesh
  or direct calls with mutual TLS

---

## Service discovery

- Use a service registry or platform-native discovery (Kubernetes DNS,
  Consul, AWS Cloud Map) — never hardcode service URLs in configuration
- Health checks MUST be implemented on every service (see
  `templates/backend/observability.md`) — the registry uses them to route
  traffic only
  to healthy instances

---

## Contract testing

- Define and test the contract between each producer and consumer using
  **consumer-driven contract tests** (e.g. Pact)
- The producer MUST NOT break a published contract without a versioned
  migration path — a failing contract test blocks the producer's deployment
- Contract tests run in CI on both the producer and the consumer side

---

## Backward compatibility

- Treat every service API as a public API — apply the same versioning and
  deprecation rules as `templates/backend/api.md`
- Use **tolerant reader** pattern: consumers ignore unknown fields; producers
  never remove fields without a deprecation period
- Add fields; never remove or rename them without a major version bump
- Event schemas follow the same rules — a schema registry (e.g. Confluent
  Schema Registry) SHOULD enforce compatibility on publish

---

## Observability

- Distributed tracing is **mandatory** in a microservices system — every
  service MUST propagate the `traceparent` header (see
  `templates/backend/observability.md`)
- Aggregate logs from all services into a single platform — searching
  across services by trace ID must be possible in under 30 seconds
- Each service exposes its own metrics; a central dashboard correlates
  them across service boundaries
- Define an SLO for each public-facing service; alert on SLO burn rate,
  not just on errors