# Backend — Wiki

Wiki notes on what a backend is, the API styles it can expose, the
building blocks you assemble it from, and how to combine those blocks
to meet requirements such as resilience, availability, and security.

This page is concept-first and maps each topic to the authoritative
rules. See `backend/http.md`, `backend/api.md`, `backend/auth.md`,
`backend/database.md`, `backend/caching.md`, `backend/jobs.md`,
`backend/messaging.md`, `backend/grpc.md`, `backend/microservices.md`,
`backend/errors.md`, `backend/observability.md`, and
`backend/monitoring.md` for the specifics.

---

## 1. What a backend is

A backend is the server-side system that owns business logic, durable
state, and integrations, and exposes them to clients through a
contract (an API). Clients — web, mobile, other services — hold no
authority of their own; they ask the backend, which decides.

Core responsibilities:

- **Accept** requests over a transport (HTTP, gRPC, a queue).
- **Authenticate** the caller — who is this? (`backend/auth.md`)
- **Authorize** the action — may they do this? (`backend/auth.md`)
- **Validate** input before it reaches logic or storage.
- **Apply** business rules — the part no client may be trusted with.
- **Persist and read** state — databases, caches, blob stores.
- **Integrate** with external systems — payments, email, other APIs.
- **Respond** with a result or a typed error (`backend/errors.md`).
- **Emit** logs, metrics, traces, events (`backend/observability.md`).

The request lifecycle runs edge → application → data and back:

```
client → [edge: TLS, gateway, rate limit, authn]
       → [application: validate, authorize, business logic]
       → [data: database, cache, blob, search]
       → [integrations / events: queues, brokers, webhooks]
       → response
```

The frontend renders and collects; the backend decides and remembers.
Anything that must be trusted, shared across clients, or kept
consistent lives in the backend.

## 2. API styles — when to use what

An API is the contract a backend exposes. The style sets its shape,
its transport, and the coupling it creates. Most systems use more
than one.

| Style | Shape | Best for | Avoid when | Rules |
|-------|-------|----------|------------|-------|
| **REST / HTTP** | Resources + verbs over HTTP | CRUD, public APIs, broad client reach, cacheable reads | Chatty multi-resource fetches; strict cross-service typing | `backend/http.md`, `backend/api.md` |
| **gRPC** | Typed RPC over HTTP/2 + protobuf | Low-latency service-to-service, streaming, polyglot internals | Browser-direct calls; public APIs needing easy curl | `backend/grpc.md` |
| **GraphQL** | Client-shaped queries on one endpoint | Aggregating many resources, varied client views, mobile | Simple CRUD; when per-field caching or rate limits matter | `backend/api.md` |
| **WebSocket / SSE** | Persistent push channel | Real-time updates, chat, live dashboards, notifications | Plain request/response; when polling is good enough | `backend/http.md` |
| **Messaging / events** | Async messages via a broker | Decoupling, fan-out, load leveling, slow work | When the caller needs an immediate answer | `backend/messaging.md`, `backend/jobs.md` |
| **Webhooks** | Backend-to-backend HTTP callbacks | Notifying third parties of events you emit | Internal comms you control end to end | `backend/webhooks.md` |

The deciding axis is **synchronous vs asynchronous**:

- **Synchronous** (REST, gRPC, GraphQL): the caller waits for the
  result. Easy to reason about; couples the caller's availability to
  yours.
- **Asynchronous** (messaging, webhooks, jobs): the caller hands off
  and moves on. Buys resilience and scale; costs eventual consistency
  and delivery/ordering concerns.

Rule of thumb: synchronous for reads and user-facing actions that need
an answer now; asynchronous for work that is slow, bursty, fan-out, or
must survive a downstream outage.

## 3. The building blocks

A backend is assembled from a small, recurring set of components. You
rarely invent new ones — you choose which to include and how to wire
them together.

| Block | Role | Stateful? | Rules |
|-------|------|-----------|-------|
| **Edge / gateway** | TLS, routing, load balancing, CDN, rate limit, authn, WAF | No | `backend/http.md` |
| **API / application layer** | Validate, authorize, run business logic | No (keep it so) | `backend/quality.md` |
| **Auth provider** | Identity, tokens, sessions, keys | Yes | `backend/auth.md` |
| **Config / secrets** | Env vars, secrets, runtime config | Yes | `base/config.md` |
| **Feature flags** | Toggles, gradual rollout, experiments | Yes | `backend/features.md` |
| **Relational DB** | Source-of-truth records, transactions | Yes | `backend/database.md` |
| **Cache / KV** | Hot reads, sessions, locks, counters | Yes (ephemeral) | `backend/caching.md` |
| **Blob store** | Files, media, large payloads | Yes | — |
| **Search index** | Full-text and faceted queries | Yes (derived) | — |
| **Analytics / warehouse** | OLAP, time-series, reporting queries | Yes (derived) | — |
| **Broker / queue** | Decouple, buffer, fan-out | Yes | `backend/messaging.md` |
| **Workers / jobs** | Async and scheduled work | No | `backend/jobs.md` |
| **Integrations** | External APIs, outbound webhooks | No | `backend/webhooks.md` |
| **Observability** | Logs, metrics, traces, health | — | `backend/observability.md`, `backend/monitoring.md` |

The most important property is **statelessness** in the application
layer: keep request-scoped state out of process memory and push
durable state into the data tier. Stateless app instances are what
make horizontal scaling, rolling deploys, and failover cheap (see §4).

## 4. Composing for requirements

You build "almost anything" by selecting blocks (§3) and switching on
a few mechanisms per cross-cutting requirement. The blocks stay the
same; the requirements decide which mechanisms you enable.

### Authentication — who is the caller?

Sessions (cookies) for browser apps; JWT/bearer tokens for APIs and
services; API keys for machine clients; OAuth2/OIDC to delegate
identity; mTLS for service-to-service. See `backend/auth.md`.

### Authorization — what may they do?

RBAC for role-shaped rules; ABAC or scopes for fine-grained and
resource-owned access. Enforce in the application layer, never on the
client. See `backend/auth.md`.

### Resilience — survive partial failure

**Timeouts** on every outbound call; **retries** with backoff and
jitter for transient faults; **idempotency keys** so retries are safe;
**circuit breakers** to stop hammering a downed dependency;
**dead-letter queues** for messages that cannot be processed;
**bulkheads** to isolate resource pools; **backpressure** to shed load
(return `429` with `Retry-After`) when saturated rather than topple.
See `backend/errors.md`, `backend/jobs.md`, `backend/caching.md`.

### High availability — survive instance or zone loss

Stateless app instances behind a load balancer; N+1 redundancy across
zones; **health checks** to gate traffic; graceful shutdown to drain
in-flight work; degrade gracefully — serve cached or partial results
rather than fail hard.

### Accessibility, part 1 — consumability

Make the backend easy and safe to consume: design API-first behind an
OpenAPI or proto contract; version and deprecate explicitly; paginate
large collections; expose rate-limit headers and typed errors; publish
docs straight from the contract. See `backend/api.md`, `backend/http.md`.

### Accessibility, part 2 — reachability

Make the backend reachable where users are: front it with an
edge/gateway and CDN; terminate TLS; use stable DNS; place capacity in
the regions you serve; keep a documented status page and fallback path.

### Scalability & performance — handle more load

Scale stateless tiers horizontally; cache hot reads (cache-aside + TTL
+ stampede control); offload slow work to jobs and queues; **coalesce**
repeated changes to one resource into a single job (debounce);
**schedule fairly** with per-tenant queues so one tenant cannot starve
the rest; add read replicas; pick async I/O or worker processes per
workload. See `backend/caching.md`, `backend/concurrency.md`,
`backend/jobs.md`.

### Consistency & data integrity

Wrap multi-step writes in a transaction within one store; across
services use sagas plus the outbox pattern for eventual consistency;
make every consumer idempotent. See `backend/database.md`,
`backend/microservices.md`.

### Observability & operability

Structured logs, the four golden signals (latency, traffic, errors,
saturation), distributed traces, and health/readiness endpoints — so
you see and alert before users do. See `backend/observability.md`,
`backend/monitoring.md`.

### Security — cross-cutting

Validate all input; least-privilege credentials; secrets from the
environment, not code; encrypt in transit and at rest. See the
`security.md` wiki page and `base/config.md`.

## 5. Reference compositions

The same blocks, combined to different ends. Each archetype is a
starting point — add mechanisms from §4 as requirements demand.

### Simple CRUD service

```
client → REST API → application → relational DB
                              └→ cache (hot reads)
```

REST + one database + a cache. Add authn/authz and pagination. Most
products start here and stay here longer than they expect.

### High-throughput ingestion

```
producers → intake API (fast-ack) → queue → workers → store
```

Accept fast, process asynchronously. The queue absorbs bursts; workers
scale independently; a DLQ catches failures. See `backend/jobs.md`,
`backend/messaging.md`.

### Event-driven microservices

```
service A → broker → service B, C   (each owns its data)
         └→ outbox ┘
```

Services communicate by events, own their own stores, and stay
consistent via sagas and the outbox pattern. Test the boundaries with
contract tests. See `backend/microservices.md`.

### Real-time application

```
clients ⇄ WebSocket/SSE gateway ⇄ application ⇄ pub/sub → DB
```

Persistent channels push updates; pub/sub fans them out across
instances; durable state still lands in a database.

### Inbound webhooks under load

```
provider → intake (verify, fast-ack 2xx) → per-tenant queues
        → bounded workers (dedup, debounce) → store
                                           └→ DLQ (jittered retry)
```

A webhook flood — a new tenant's initial sync, a bulk edit, a chatty
provider firing per keystroke — is not a new problem but a composition
of the blocks above. Processing inline would let provider retries
amplify a spike into an outage; instead compose:

- **Fast-ack:** verify the signature, enqueue, return `2xx` within the
  provider's timeout — no heavy work on the request path.
- **Idempotency:** dedupe on the provider's event ID (TTL = the retry
  window); at-least-once delivery guarantees duplicates.
- **Debounce:** collapse a chatty source's repeated edits to one
  resource into a single job after a quiet period.
- **Bounded workers + backpressure:** cap concurrency to protect
  downstreams; return `429` when saturated.
- **Per-tenant fairness:** separate queues so one large account cannot
  starve the rest.
- **DLQ:** park poison events after N jittered retries for later replay.

See `backend/webhooks.md` and `backend/messaging.md` for the rules.

The lesson: a handful of blocks (§3) plus a handful of mechanisms (§4)
compose into the vast majority of backends. Reach for a new style or
component only when a concrete requirement forces it.
