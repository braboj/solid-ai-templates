# Backend — Observability
[ID: backend-observability]

## Logging

### Log levels
Use the correct level — do not elevate debug information to INFO:

| Level | When to use | Examples |
|-------|-------------|---------|
| FATAL | App cannot continue — imminent shutdown | Out of memory, missing critical dependency at startup, DB schema mismatch |
| ERROR | Operation failed — normal flow disrupted | Failed DB write, file not found, unhandled exception in request handler |
| WARN | Unexpected but recoverable — may lead to error | Low disk space, slow response, retry attempt, deprecated endpoint accessed |
| INFO | Normal operation — confirm correct functioning | Order accepted, service started, payment processed, scheduled job completed |
| DEBUG | Technical detail for debugging — not for production | Query results, data mapping steps, connection established |
| TRACE | Most verbose — step-by-step tracing, development only | Function parameters, pipeline steps, request/response payloads |

- Default log level in all environments: **INFO**
- DEBUG and TRACE MUST NOT be enabled in production by default
- INFO MUST NOT contain debug or trace information — keep it operational

### Log format
- Use structured logging in all environments: JSON in production,
  human-readable in development
- Every log entry MUST include: timestamp, level, message, properties
- Include a request ID in all log entries for a given request lifecycle
- Minimum JSON structure:
  ```json
  {
    "Timestamp": "2024-01-15T12:34:56.789Z",
    "Level": "Information",
    "MessageTemplate": "Order ({orderId}) accepted.",
    "Message": "Order (ORD-78901) accepted.",
    "Properties": { "orderId": "ORD-78901" }
  }
  ```

### Rules
- Log errors once — at the top of the call stack, not at every level
- Never log sensitive data: passwords, tokens, API keys, PII
- Client errors (4xx) — log at INFO
- Server errors (5xx) — log at ERROR
- All unhandled errors MUST be logged with enough context to reproduce the issue

## Distributed tracing

- Assign a unique **trace ID** to every inbound request at the service boundary
- Propagate the trace ID in all outbound calls (HTTP headers, message queue
  metadata) using the W3C `traceparent` header or OpenTelemetry context
- Include the trace ID in every log entry for that request — use the same
  field name across all services (`trace_id`)
- Use OpenTelemetry as the instrumentation standard — avoid vendor-specific
  SDKs in application code; export to the backend of choice (Jaeger, Tempo,
  Datadog, etc.) via the OTel collector
- Create spans for: inbound HTTP requests, outbound HTTP calls, DB queries,
  cache operations, and background job execution
- Span names MUST be low-cardinality — use route templates, not URLs with IDs
  (e.g. `GET /users/{id}`, not `GET /users/42`)
- Return the trace ID in error responses (`X-Trace-Id` header) so clients
  can report it to support

## Health check
- Expose a health check endpoint: `/health` or `/healthz`
- Return HTTP 200 when the service is ready to handle traffic
- Return HTTP 503 when a critical dependency (DB, cache) is unavailable
- Health check MUST NOT require authentication
- Health check MUST be the first thing that passes before traffic is routed
  to a new instance

## Error visibility
- Distinguish between client errors (4xx) and server errors (5xx) in logs
- Include correlation/request IDs in error responses to enable log tracing
- Never expose internal state, stack traces, or file paths in error responses

## Pipeline diagnosability

Multi-stage pipelines (ETL, data/image extraction, compiler passes, build
tools) hide their failures: when a stage produces wrong output, the only
visible artifacts are the input and the final result, so every "this
looks wrong" becomes a probe session reconstructing intermediate state.

- Accept an optional diagnostic sink (a `DiagnosticSink` Protocol or
  interface) as a pipeline parameter; each stage calls
  `sink.record_<stage>(artifact)` only when a sink is supplied
- Provide a `FileDiagnosticSink` that writes one named artifact per stage
  (image, mask, table, AST, JSON) to a known directory for inspection
- Contract: pipeline output MUST be byte-identical with or without a sink
  — the diagnostic concern lives outside the core path, never alters it
- Diagnostic artifacts are gitignored — on-demand debugging output, not
  committed state
- Reach for this when stages have named, inspectable intermediate
  artifacts, failure reports describe symptoms rather than stages, and a
  change can break one stage silently while the final output still looks
  plausible