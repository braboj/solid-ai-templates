# Backend — gRPC
[ID: backend-grpc]
[DEPENDS ON: templates/backend/auth.md, templates/backend/observability.md]

Cross-cutting rules for gRPC services backed by Protocol Buffers. Applies
regardless of implementation language. Language-specific stacks extend this
file with runtime conventions, project structure, and tooling.

---

## When to use gRPC

- Use gRPC for synchronous service-to-service communication where performance,
  strong typing, or streaming are required
- Use gRPC when a shared proto schema across multiple language runtimes is
  preferable to maintaining multiple OpenAPI specs
- Do NOT use gRPC as the primary API for browser clients — use REST or GraphQL
  at the edge and gRPC internally

---

## Proto design
[ID: grpc-proto]

- Package all protos under a versioned namespace: `package [org].[service].v1`
- One proto file per service — do not mix unrelated services in one file
- Field names in `snake_case` — generated code adapts to each language's
  conventions
- Use `google.protobuf.Timestamp` for all timestamps — never raw integers
- Use `google.protobuf.FieldMask` for partial update (patch) operations
- Never remove or renumber existing fields — mark deprecated fields with
  `[deprecated = true]` and reserve the number: `reserved 4;`
- Breaking changes require a new package version (`v2`) — serve the old
  version until all consumers have migrated

---

## Service implementation
[ID: grpc-implementation]

- Service handlers are thin — decode the request, call a domain service
  function, encode the response; no business logic in the handler
- Domain service functions have no gRPC imports — independently testable
- Validate request messages at the handler entry point; return
  `INVALID_ARGUMENT` for missing or malformed fields

### Status codes

| Situation | Code |
|-----------|------|
| Missing or invalid field | `INVALID_ARGUMENT` |
| Resource not found | `NOT_FOUND` |
| Caller not authenticated | `UNAUTHENTICATED` |
| Caller lacks permission | `PERMISSION_DENIED` |
| Conflicting state | `ALREADY_EXISTS` / `ABORTED` |
| Transient infrastructure error | `UNAVAILABLE` |
| Unexpected error | `INTERNAL` |

---

## Interceptors
[ID: grpc-interceptors]

- **Auth**: validate token on every call — reject with `UNAUTHENTICATED`
  before the handler runs
- **Logging**: log method name, request ID, caller identity, duration, and
  status code for every call
- **Tracing**: propagate W3C `traceparent` via gRPC metadata using
  OpenTelemetry gRPC instrumentation
- **Recovery**: catch unhandled panics or exceptions — return `INTERNAL`,
  never crash the server process
- Register all interceptors as a chain at server startup — not inside handlers

---

## Authentication
[EXTEND: backend-auth]

- Pass credentials via gRPC metadata: key `authorization`, value `Bearer
  <token>`
- Validate in the auth interceptor — not in service handlers
- Mutual TLS (mTLS) for service-to-service calls in production — certificate
  rotation managed at the infrastructure layer (cert-manager, Vault)
- Plaintext only in local development — never in staging or production

---

## Observability
[EXTEND: backend-observability]

- Expose Prometheus metrics on a separate HTTP port (`/metrics`):
  - `grpc_server_handled_total` — labelled by method and status code
  - `grpc_server_handling_seconds` — histogram, labelled by method
- Implement the standard gRPC Health Checking Protocol
  (`grpc.health.v1.Health`) — required for Kubernetes probes
- Propagate trace context through gRPC metadata for distributed tracing

---

## Testing
[ID: grpc-testing]
[EXTEND: base-testing]

- Unit-test domain service functions independently of gRPC — pass plain
  request structs/objects, assert plain response structs/objects
- Integration tests: start an in-process gRPC server and call it with a
  real client — test each method for success, invalid argument, and auth failure
- Test naming: `<MethodName>_<state>_<expected>`
  e.g. `GetUser_UserNotFound_ReturnsNotFoundStatus`

---

## Proto tooling
[ID: grpc-tooling]

- Lint protos with `buf lint` in CI — enforce naming, field numbering, and
  style consistency
- Detect breaking changes with `buf breaking --against` in CI — reject PRs
  that introduce wire-incompatible changes without a version bump
- Generate stubs in CI — if generated code is committed, regenerate and commit
  in the same PR as the proto change; never let protos and stubs diverge
