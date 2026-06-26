# Backend — Error Handling
[ID: backend-errors]
[DEPENDS ON: templates/backend/http.md, templates/backend/observability.md]

Error response format and logging rules are defined in
`templates/backend/http.md` and
`templates/backend/observability.md`. This template covers classification,
propagation,
and recovery.

---

## Error classification

Classify every error before handling it — the class determines the response,
the log level, and the recovery strategy:

| Class | Cause | HTTP range | Log level |
|-------|-------|------------|-----------|
| **Validation** | Invalid input from the caller | 400, 422 | INFO |
| **Authentication** | Missing or invalid credentials | 401 | INFO |
| **Authorization** | Valid credentials, insufficient permission | 403 | INFO |
| **Not found** | Resource does not exist | 404 | INFO |
| **Conflict** | State violation (duplicate, stale write) | 409 | INFO |
| **Infrastructure** | DB, cache, or queue unavailable | 503 | ERROR |
| **External** | Third-party API or service failure | 502, 504 | ERROR |
| **Unexpected** | Unhandled exception, programming error | 500 | ERROR |

- Never map an infrastructure or unexpected error to a 4xx — that misleads
  the caller about who is responsible
- Never map a validation error to a 5xx — the caller must know the request
  was rejected, not that the server failed

---

## Propagation through layers

- **Repository layer**: raise typed, domain-agnostic errors
  (e.g. `RecordNotFound`, `ConnectionError`) — never expose ORM or driver
  exceptions to the layers above
- **Service layer**: catch repository errors and re-raise as domain errors
  (e.g. `OrderNotFound`, `PaymentServiceUnavailable`); add business context
  before re-raising
- **Handler layer**: catch domain errors, map them to HTTP responses using a
  central error mapper — no ad-hoc `try/except` per route
- Log once, at the handler or middleware boundary — never log the same error
  at multiple layers

---

## Recovery and graceful degradation

- Wrap all outbound calls (HTTP, DB, cache, queue) in a timeout — never wait
  indefinitely for an external response
- Use the **Circuit Breaker** pattern for repeated calls to external services
  — fail fast after a threshold of failures; recover automatically after a
  cool-down period
- Degrade gracefully when a non-critical dependency is unavailable — serve
  a reduced response rather than failing the entire request
  (e.g. return cached data if the live source is down)
- Non-idempotent operations that fail mid-way MUST leave the system in a
  consistent state — use transactions or compensating actions; never leave
  partial writes uncommitted

---

## External service failures

- Never surface a third-party error message directly to the caller — translate
  it into a domain error with a message you control
- Distinguish between a timeout (client waited too long) and a rejection
  (external service actively refused) — use 504 for timeout, 502 for rejection
- Log the full external error response at ERROR level for diagnosis; return
  only a safe, generic message to the caller
- Implement retry with exponential backoff and jitter for transient external
  failures — do not retry on 4xx responses from the external service

---

## Unexpected errors

- All unhandled exceptions MUST be caught at the outermost middleware boundary
  — no exception should escape to the framework's default handler
- Return a generic 500 response with a trace ID — never return a stack trace,
  internal path, or error message that reveals implementation details
- Treat every unexpected error as a bug — create a ticket, do not suppress