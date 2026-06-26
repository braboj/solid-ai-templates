# Backend — Quality Attributes
[ID: backend-quality]
[DEPENDS ON: templates/base/core/quality.md, templates/base/core/oop.md, templates/base/security/security.md, templates/base/infra/containers.md]

## Layered architecture
- Enforce a strict handler → service → repository separation
- No database access in handlers — always go through the service layer
- No HTTP concerns in the service layer — services are framework-agnostic
- Domain logic lives in the service layer, not in models or schemas

## Design patterns

Prefer these patterns for backend concerns:

- **Repository** — abstract all data access behind a repository interface;
  the service layer never constructs queries directly
- **Service layer** — encapsulate business logic in stateless service objects;
  one service per domain aggregate
- **Unit of Work** — coordinate multiple repository operations in a single
  transaction; commit or roll back as one atomic unit
- **Factory / Factory Method** — centralise object construction, especially
  for domain objects with complex invariants
- **Strategy** — swap algorithms or business rules (pricing, validation,
  export format) at runtime without modifying the caller
- **Observer / Event** — decouple producers from consumers for domain events
  (user registered, order placed); use an internal event bus or message queue
- **Circuit Breaker** — wrap all outbound calls to external services;
  fail fast and recover gracefully rather than cascading timeouts
- **Outbox** — when publishing an event must be atomic with a DB write,
  write to an outbox table in the same transaction and relay asynchronously
- **CQRS** — separate read models from write models when query and command
  requirements diverge significantly; do not apply by default

## Disposability

- Processes MUST start fast — minimize initialization time
- Processes MUST shut down gracefully on `SIGTERM` — finish
  in-flight work, release resources, then exit
- Set a shutdown timeout — if graceful shutdown exceeds the
  deadline, force-exit
- Design for crash safety — the system MUST recover cleanly if
  a process is killed without warning (`SIGKILL`, power loss)
- Do not store state in-process — use external stores (database,
  cache, queue) so processes are disposable and replaceable

## Admin processes

- One-off tasks (migrations, data fixes, REPL sessions) MUST run
  in the same environment as the application — same code, same
  config, same dependencies
- Admin scripts MUST be committed to the repository — not run
  from ad-hoc shell commands
- Prefer idempotent scripts — safe to re-run without side effects
- Never run admin tasks directly against production without a
  tested rollback plan

## Security
[EXTEND: security-input]

- Rate-limit public endpoints — never expose unbounded write operations
- Apply authentication and authorisation before any business logic
  executes

## Performance
- Prefer async I/O for network-bound operations
- Cache only when there is a measured need — document cache invalidation
  strategy
- Avoid N+1 queries — use eager loading or batch fetching
- Set timeouts on all outbound calls (HTTP clients, DB queries)

## API stability
- Never remove or rename a field in a response without a deprecation period
- Increment the API version (`/v2/`) for breaking changes — keep the old version
  alive
- Document deprecated endpoints; set a removal date before retiring them