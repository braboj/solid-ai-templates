# MetricsHub

Infrastructure metrics collection and aggregation service.

- Owner: Infrastructure team
- Repo: github.com/acme/metricshub
- Deployment: Docker image -> Kubernetes (cloud)
- Model: inline

> Generation inputs (per ADR-016 — examples are agent-generated
> outputs of the documented pipeline):
>
> - Stack source: `stack/go-echo.md` (-> go-service -> go-lib) +
>   `backend/auth.md` (JWT depth not in the resolved chain — inlined)
> - Resolved chain: `generated/stack-go-echo.md` (base + backend +
>   go-echo)
> - Output format: `base/core/agents.md` (inline model)
> - Project brief: MetricsHub — Infrastructure team — Go 1.22 / Echo
>   v4 / PostgreSQL via sqlc + pgx / JWT bearer auth / OpenFeature
>   feature flags — go test, golangci-lint, Docker on Kubernetes

This file is self-contained: all rules are inlined, no external
templates need to be read.

## 1. Project

### 1.1 Overview

- Model: inline
- Language: Go 1.22+
- HTTP framework: Echo v4
- Database: PostgreSQL via sqlc + pgx
- Config: github.com/caarlos0/env
- Test runner: go test (stdlib)
- Auth: JWT bearer tokens
- Feature flags: OpenFeature Go SDK
- Containerisation: Docker
- Distribution: Docker image -> Kubernetes

### 1.2 Project structure

```
cmd/
  metricshub/
    main.go              # entry point — wires deps, starts server
internal/
  metrics/
    handler.go           # HTTP handlers (thin)
    service.go           # business logic
    repository.go        # data access (sqlc-generated + pgx)
    model.go             # domain types
  config/
    config.go            # Config struct, loaded from env at startup
  server/
    server.go            # Echo instance, middleware, routing
pkg/                     # code safe to import externally (if any)
migrations/              # SQL migration files
Dockerfile
Makefile
go.mod
go.sum
README.md
CLAUDE.md
```

- `internal/` enforces encapsulation — external packages cannot
  import it
- `cmd/` is thin — no business logic, only wiring
- One domain concern per package — no `utils/` or `helpers/` packages

### 1.3 Commands

```bash
go run ./cmd/metricshub           # develop
go build ./cmd/metricshub         # build binary
go test ./...                     # run all tests
go test -race ./...               # run with the race detector
go test -tags integration ./...   # run integration tests
go vet ./...                      # static analysis
goimports -w .                    # format imports
staticcheck ./...                 # additional static analysis
make migrate-up                   # apply DB migrations
docker build -t metricshub .      # build container image
```

## 2. Code conventions

### 2.1 Git

- Branch: `main` (protected) — never commit directly
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`,
  `docs/<scope>`
- Commits: `<type>(<scope>): <summary>` — types: feat, fix, chore,
  docs, refactor, style, test; subject under 80 characters,
  imperative mood
- PRs are small and focused — one concern per PR; review the diff and
  confirm CI is green before merge
- Repeat the closing keyword before each issue number:
  `Closes #a, closes #b` — a bare `#b` stays open
- Never force-push a branch, including with `--force-with-lease`; when
  behind `main`, merge `main` in or use `gh pr update-branch`
- After a PR is merged, delete the branch and pull `main` before new
  work
- Do not commit compiled binaries, `*.test` files, build output,
  secrets, or `vendor/` (unless vendoring is an explicit decision —
  document it in README)
- `go.sum` is committed — do not delete or regenerate without cause
- Tag releases with `vX.Y.Z` — the Go module proxy uses these
- Migrations are committed — never edit or regenerate a migration
  already merged
- Every repository MUST have a `.gitignore` and a committed lockfile

### 2.2 Go

- Follow Effective Go and Go Code Review Comments — the canonical
  style references
- `gofmt` / `goimports` — code MUST be formatted; CI rejects
  unformatted code
- Run `go vet ./...` — fix all warnings before committing
- Run `staticcheck ./...` for additional static analysis
- No unused imports or variables — the compiler rejects these
- Exported symbols MUST have a doc comment
- Small, focused packages — one domain concern per package
- Define interfaces where the caller owns them; keep them 1–3 methods
- Accept interfaces, return concrete types
- Avoid package-level `init()` — initialise explicitly in `main`
- Always handle errors — never `_` discard an error return
- Wrap errors with context: `fmt.Errorf("creating metric: %w", err)`
- Use `errors.Is()` and `errors.As()` for inspection — never string
  matching
- Define sentinel errors (`var ErrNotFound = errors.New(...)`) in the
  package that owns the concept
- Cognitive complexity <= 15 per function; maximum nesting depth of
  three — use early returns and guard clauses
- No debug statements (`fmt.Println`) in committed code
- Source files UTF-8, ASCII content only, LF line endings

### 2.3 Application setup

- One `Echo` instance created in `internal/server/server.go`
- Register all routes and middleware in `server.go` — no scattered
  `e.GET(...)` calls across packages
- `main.go` owns startup and shutdown orchestration — wire
  dependencies, start the server, handle signals
- Processes MUST start fast and shut down gracefully on `SIGTERM`
- Do not store state in-process — use PostgreSQL so processes are
  disposable

### 2.4 Configuration

- One `Config` struct in `internal/config/config.go` — loaded from
  env vars at startup; passed explicitly through the dependency graph
- Never read `os.Getenv` directly in application code outside the
  config loader
- Validate all required config at load time — fail fast if anything
  is missing or invalid
- `SCREAMING_SNAKE_CASE` env vars, prefixed `METRICSHUB_` to avoid
  collisions (e.g. `METRICSHUB_DATABASE_URL`, `METRICSHUB_PORT`)
- The port MUST be configurable via environment variable — never
  hardcoded
- `.env.example` committed with placeholders; `.env` in `.gitignore`
- Mark all secrets as required — no defaults for passwords, tokens,
  or keys; never log config values

### 2.5 Routing

- Define all routes in `internal/server/server.go` — one place, no
  scattered `e.GET(...)` calls across packages
- Group routes by resource: `e.Group("/api/v1/metrics")` — apply
  middleware at group level, not per-route
- Use named path parameters: `e.GET("/metrics/:id", handler)` —
  access via `c.Param("id")`
- Version all API routes under a prefix: `/api/v1/`, `/api/v2/`
- Path segments MUST be lowercase plural nouns with hyphens, no
  verbs, no trailing slash; query parameter names use camelCase
- JSON is the default format; date/time values use ISO 8601
- All traffic served over HTTPS — plain HTTP is not acceptable

### 2.6 Handlers

- Handler signature: `func (h *Handler) Create(c echo.Context) error`
- Handlers are thin — decode request, call service, encode response;
  all business logic belongs in the service layer
- Bind and validate in one step: `c.Bind(&req)` then call a validator
  — never trust unbound input
- Return errors with `c.JSON(code, resp)` or by returning an
  `*echo.HTTPError` — never write directly to `c.Response()`
- Enforce a strict handler -> service -> repository separation; no
  database access in handlers
- No unbounded list endpoints — always paginate with an explicit
  limit

### 2.7 Request binding and validation

- Use the `echo.Validator` interface — register a single validator at
  startup (e.g. `go-playground/validator`)
- Call `c.Validate(req)` after `c.Bind(req)` in every handler that
  receives a body
- Treat binding errors and validation errors as `400 Bad Request` —
  return a structured JSON body, not a plain string
- Never use `json.Decoder` directly in handlers — let Echo's binder
  handle it
- Validate all external input at the system boundary; allowlist, not
  blocklist — reject everything not explicitly valid
- Internal code trusts validated data — do not re-validate in the
  service or repository layers

### 2.8 Middleware

- Use `echo/middleware` for `RequestID`, `Logger`, `Recover`, `CORS`,
  and `RateLimiter` — configure globally on the root `Echo` instance
- Write custom middleware as `echo.MiddlewareFunc` — keep it
  stateless; inject dependencies via closure
- Order matters: `Recover` -> `RequestID` -> `Logger` -> auth ->
  business middleware
- Never put business logic in middleware
- Set security headers at the middleware level, not per route; rate-
  limit public endpoints

### 2.9 Error handling

- Register a custom `Echo.HTTPErrorHandler` — all errors flow through
  one place
- Map sentinel errors (e.g. `ErrNotFound`) to HTTP status codes in
  the error handler, not in individual handlers
- Return `*echo.HTTPError` for expected errors; let the error handler
  convert unexpected errors to `500`
- Include `request_id` in every error response body for traceability
- Classify every error before handling it — the class sets the HTTP
  status and log level:
  - Validation -> 400/422, log INFO
  - Authentication -> 401, log INFO
  - Authorization -> 403, log INFO
  - Not found -> 404, log INFO
  - Conflict -> 409, log INFO
  - Infrastructure (DB/cache down) -> 503, log ERROR
  - External service failure -> 502/504, log ERROR
  - Unexpected -> 500, log ERROR
- Repository layer raises typed, domain-agnostic errors; service
  layer adds business context; handler layer maps to HTTP — log once,
  at the handler or middleware boundary
- Follow RFC 9457 (`application/problem+json`) for the error body
  shape; never use 200 for an error
- Never return stack traces, internal paths, or implementation
  details to the client
- Wrap all outbound calls (HTTP, DB) in a timeout; use a circuit
  breaker for repeated calls to external services

### 2.10 Concurrency and graceful shutdown

- Protect shared state with `sync.Mutex` or `sync.RWMutex` — document
  which fields are guarded by which lock
- Never hold a lock while performing I/O — risk of deadlock and
  contention
- Always use `context.Context` as the first argument in functions
  that may block; propagate cancellation explicitly
- Use `errgroup` for structured concurrency — all goroutines started
  in `main.go` under one group, stopped cleanly on context
  cancellation
- Never start a goroutine without a clear owner and a clear way to
  stop it
- Graceful shutdown: listen for `SIGTERM`, call server shutdown,
  drain in-flight requests, then cancel the root context
- Run tests with `go test -race` in CI — do not rely on review alone
  to catch data races

### 2.11 Authentication and authorization

- JWT bearer tokens validated in a shared Echo middleware dependency
  — centralise auth logic, no scattered permission checks
- Authentication (who) and authorization (what) are separate
  concerns — keep them in separate layers
- Never implement cryptographic primitives — use well-audited
  libraries; fail closed (deny by default, grant explicitly)
- Validate every JWT: signature, `exp`, `iss`, `aud` — reject tokens
  missing any required claim
- Token lifetime: access <= 15 min, refresh <= 7 days (rotated on
  use); store refresh tokens server-side so they can be revoked
- Access tokens MUST arrive in `Authorization: Bearer <token>` —
  never in query parameters; refresh tokens in `httpOnly`, `Secure`,
  `SameSite=Strict` cookies
- Use RBAC as the baseline; layer ABAC on top for fine-grained needs
- Authorise at the service layer, not only at the route layer — a
  route that passes auth may call a service touching another user's
  data
- Never trust client-supplied IDs for ownership checks — verify the
  authenticated user owns the requested resource
- Never log or expose token payloads, passwords, or secrets in error
  responses or logs — even at DEBUG level
- Log auth failures at WARN with IP and user agent (never the
  attempted password); alert on a spike

### 2.12 Feature flags

- Use the OpenFeature Go SDK — wrap the provider behind an interface
  so it can be swapped in tests
- Pass the flag client through the dependency graph — a constructor
  argument, not a package-level singleton
- In tests, use the in-memory OpenFeature provider
- Every flag has an owner and a removal date set at creation time —
  flags without a removal date are not allowed to merge
- Remove the flag and its dead branch as soon as the rollout is
  complete — stale flags are technical debt
- Never nest feature flags — a flag that activates only when another
  is active creates untestable combinations
- Keep the flagged code path as small as possible — wrap the decision
  point, not the whole function
- Flags are evaluated at runtime, not at startup — never cache a flag
  value for longer than one request lifecycle unless the cost is
  measured and justified
- Evaluate flags at the entry point of the feature — handler or
  service layer, never deep inside domain logic
- Return the same response shape for both flag states; treat the
  flag-off path as the production default until the flag is removed
- Log which variant was evaluated per flagged request; fail to the
  safe default and alert if flag evaluation fails

## 3. Quality

### 3.1 Testing

- Use the stdlib `testing` package — no third-party assertion
  libraries
- Table-driven tests with `t.Run()` for parameterised cases
- Test the public API of each package — not unexported functions
- Use interfaces to inject dependencies in tests — no monkey-patching
- Test naming: `Test<UnitOfWork>_<State>_<Expected>` — e.g.
  `TestGetMetric_NotFound_Returns404`
- Use `net/http/httptest` with `echo.New()` — no real server needed
  for unit tests; call handlers via `e.ServeHTTP(rec, req)` and
  assert on `rec.Code` and `rec.Body`
- Integration tests use a real Echo server on a random port — start
  in `TestMain`, share across test functions
- Integration tests live in `internal/metrics/*_integration_test.go`
  behind a build tag: `//go:build integration`
- No database mocking in integration tests — use a real test
  PostgreSQL; reset state (truncate or rollback) between runs; never
  substitute SQLite
- Test auth: assert 401 for unauthenticated and 403 for
  insufficient-permission requests; assert expired and revoked tokens
  are rejected
- New code MUST reach 90% coverage; total coverage MUST NOT regress
  and SHOULD stay at or above 80%
- Run before every commit: `go test ./... && go vet ./...`

### 3.2 Observability

- Structured JSON logs in production, human-readable in development;
  every entry includes timestamp, level, message, and the
  `request_id` for that lifecycle
- Default log level INFO in all environments — DEBUG and TRACE off in
  production
- Log errors once, at the top of the call stack; 4xx at INFO, 5xx at
  ERROR; never log passwords, tokens, API keys, or PII
- Expose `/healthz` — returns 200 when ready, 503 when a critical
  dependency (PostgreSQL) is unavailable; requires no authentication
- Assign a trace ID at the service boundary, propagate it via the W3C
  `traceparent` header, and return it on errors (`X-Trace-Id`)
- Instrument with OpenTelemetry; span names use route templates, not
  URLs with IDs (`GET /metrics/:id`, not `GET /metrics/42`)

### 3.3 Quality gates

- Lint: golangci-lint (`.golangci.yml`) at editor, pre-commit, and CI
- Format: gofmt (`gofmt -l` fails CI on unformatted code)
- Type check: `go vet ./...`
- Security: govulncheck + platform SAST; secrets: gitleaks
  (pre-commit + CI)
- Tests: `go test ./...`; coverage `go test -cover` >= 80%
- Build MUST succeed; lint errors, type errors, and high/critical
  security findings are zero-tolerance — CI fails

## 4. Identity

Not applicable — this project has no design system or brand voice.
MetricsHub is a backend service; its public contract is the HTTP API
under `/api/v1/`.

## 5. Review process

### 5.1 Code review

Before merging, review the diff against the base branch in priority
order (highest first):

1. Security — auth validated and enforced at the service layer, no
   secrets or token payloads in logs, HTTPS-only, no client-trusted
   ownership checks, parameterised queries only
2. Correctness — handlers thin, strict handler -> service ->
   repository separation, errors classified and mapped through the
   central handler, contexts and locks used correctly, goroutines
   have a clear shutdown path
3. Clarity — names are self-documenting, functions single-purpose,
   cognitive complexity <= 15
4. Conventions — gofmt / go vet / staticcheck clean, Effective Go
   idioms, URI and query-parameter casing rules, RFC 9457 error shape

Confirm CI is green. Only merge after the review passes.

### 5.2 Structure audit

- Run `go test ./... && go vet ./...` before every PR
- Verify all routes are registered in `internal/server/server.go` and
  every body-bearing handler calls `c.Bind` then `c.Validate`
- Verify `.env.example` lists every required variable and `README.md`
  documents the env reference and commands
- Verify new endpoints have success, 400/422, 401/403, and 404 tests,
  and that every feature flag has an owner and removal date
- Run the audit after: new project, migration, a new feature domain,
  or before a release

## 6. Session protocol

### 6.1 Start of session

1. Read this `CLAUDE.md` and `README.md` in full before the first
   change
2. Check the current branch — if not `main`, ask why before
   proceeding
3. Check `git status` — if uncommitted changes exist, ship the
   previous session's wrap (branch, commit, push, merge) before any
   new work
4. Clean up stale branches: `git fetch --prune`, then delete local
   branches whose PRs have merged
5. Check the latest CI/CD deploy on `main` completed successfully —
   flag if stuck, failed, or pending
6. Confirm the scope with the user before making changes
7. If the task is ambiguous, ask: "What is the specific deliverable
   for this session?"
8. Review open issues related to the agreed scope before writing code

### 6.2 During the session

- Flag explicitly when a task grows beyond the agreed scope — do not
  silently absorb new requests
- Finishing and committing the current work takes priority over
  starting something new
- Run `go test ./... && go vet ./...` after every change — do not
  accumulate unverified changes
- When a tool (formatter, sqlc generate, migration tool) touches
  unrelated files, revert the drift before committing and file it
  separately

### 6.3 End of session

When the user signals end of session ("wrap up", "let's finish", "end
session", "close out", or similar), print the full checklist below and
execute each item sequentially. Mark each item done (with result)
before moving to the next. Do not batch, skip, or summarize — visible
sequential execution prevents missed steps.

1. Commits and push — all changes committed and pushed (via PR if
   branch-protected)
2. Close issues — close completed issues (verify auto-close worked)
3. Epic checklists — update epic checklists if relevant
4. Dev journal — add a session entry to `docs/dev-journal.md` (date,
   tool, key changes, PRs merged, issues closed/created)
5. ADRs — record any architectural decisions in `docs/decisions/`; a
   new directory or content move between documents each needs an ADR
6. Migrations — confirm every schema change has a reversible
   migration committed and applied (`make migrate-up`)
7. CLAUDE.md — for each new convention, decide whether it belongs here
   (a rule the agent MUST apply every turn) or in another doc; keep
   each rule to one line
8. README.md — for each new command, dependency, or env var, confirm
   it is reflected; name the section
9. docs/ONBOARDING.md — for each new tool, prerequisite, or setup
   step, confirm it is documented; name the section
10. docs/PLAYBOOK.md — for each new command, script, or workflow,
    confirm it is documented; name the section
11. Tests and vet — run `go test ./... && go vet ./...` and confirm
    both pass
12. Flag gaps — if any item cannot be completed this session, report
    it as pending (never as done) before closing
13. Summary — summarize what was done and what is next
