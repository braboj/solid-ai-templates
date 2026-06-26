# MetricStream

Metrics ingestion service. Receives time-series data points from client
SDKs over HTTP, aggregates them in memory, and flushes to a PostgreSQL
time-series table on a configurable interval.

- Owner: Observability platform team
- Repo: github.com/acme/metricstream
- Deployment: Docker image (GHCR) -> Kubernetes (production), Docker
  Compose (local)
- Model: inline

> Generation inputs (per ADR-016 — examples are agent-generated
> outputs of the documented pipeline):
>
> - Stack source: `stack/go-service.md` + `backend/caching.md` +
>   `backend/jobs.md`
> - Resolved chain: `generated/stack-go-service.md` (base + backend +
>   go-service); `backend/caching.md` and `backend/jobs.md` are not in
>   the go-service chain, so their rules are inlined directly into
>   sections 2.9 and 2.10
> - Output format: `base/core/agents.md` (inline model)
> - Project brief: MetricStream — Observability platform team — Go 1.22
>   / chi router / PostgreSQL via pgx / Redis via go-redis / env config
>   — go test, golangci-lint, govulncheck — Docker on Kubernetes

This file is self-contained: all rules are inlined, no external
templates need to be read.

## 1. Project

### 1.1 Overview

- Model: inline
- Language: Go 1.22+
- HTTP router: chi
- Database: PostgreSQL 16 via `pgx/v5` (direct, no ORM)
- Cache: Redis 7 via `go-redis/v9`
- Config: `github.com/caarlos0/env` (struct tags, no Viper)
- Test runner: go test (stdlib)
- Static analysis: go vet, staticcheck, golangci-lint, govulncheck
- Migrations: goose (SQL files in `migrations/`)
- Containerisation: Docker (multi-stage)
- Distribution: Docker image pushed to GHCR, deployed on Kubernetes

### 1.2 Project structure

```
cmd/
  metricstream/
    main.go              # wires dependencies, starts HTTP server +
                         #   flush worker under one errgroup
internal/
  ingest/
    handler.go           # POST /v1/metrics — thin, decodes and validates
    service.go           # aggregation logic
    repository.go        # idempotency lookups (Redis)
    model.go             # DataPoint, AggregatedMetric types
  flush/
    worker.go            # periodic flush goroutine
    repository.go        # PostgreSQL write
  health/
    handler.go           # GET /health, GET /ready
  config/
    config.go            # Config struct, loaded from env at startup
  server/
    server.go            # chi router setup, middleware, graceful shutdown
pkg/                     # code safe to import externally (if any)
migrations/              # SQL migration files (goose)
tests/
  performance/           # k6 load scripts
Makefile
Dockerfile
docker-compose.yml
go.mod
go.sum
README.md
CLAUDE.md
```

- `internal/` enforces encapsulation — external packages cannot import it
- `cmd/metricstream/main.go` is thin: load config, construct
  dependencies, start server — no business logic
- One package per feature domain — name packages by domain, never
  `utils/` or `helpers/`

### 1.3 Commands

```bash
go run ./cmd/metricstream                 # develop
go build -o bin/metricstream ./cmd/metricstream   # build binary
go test ./...                             # run all tests
go test -race ./...                       # run tests with race detector
go test -tags integration ./...           # integration tests (needs Docker)
go vet ./...                              # static analysis
staticcheck ./...                        # additional static analysis
goimports -w .                           # format imports
govulncheck ./...                        # vulnerability scan
make migrate-up                          # apply DB migrations (goose up)
make migrate-down                        # roll back last migration
docker compose up                        # full local stack
docker build -t metricstream .           # build container image
```

## 2. Code conventions

### 2.1 Git

- Branch: `main` (protected) — never commit directly
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`,
  `docs/<scope>`
- Commits: `<type>(<scope>): <summary>` — types: feat, fix, chore,
  docs, refactor, test; subject under 80 characters, imperative mood
- PRs are small and focused — one concern per PR; require one approval
  and passing CI before merge
- Repeat the closing keyword before each issue number:
  `Closes #a, closes #b` — a bare `#b` stays open
- Never force-push a branch, including with `--force-with-lease`; when
  behind `main`, merge `main` in or use `gh pr update-branch`
- After a PR is merged, delete the branch and pull `main` before new work
- Do not commit compiled binaries, `*.test` files, or `.env`
- `go.sum` is committed — do not delete or regenerate without cause
- goose migrations are committed — never edit a migration already merged
- Tag releases with `vX.Y.Z` — the Go module proxy uses these
- Every repository MUST have a `.gitignore` and the committed `go.sum`

### 2.2 Go

- Follow Effective Go and Go Code Review Comments — the canonical style
  references; fix the code, never suppress a linter to dodge style
- `gofmt` / `goimports` clean — CI rejects unformatted code
- Run `go vet ./...` and `staticcheck ./...` — fix every warning before
  committing
- No unused imports or variables — the compiler rejects these
- Exported symbols MUST have a doc comment
- Names are the primary documentation; cognitive complexity <= 15 per
  function, maximum nesting depth of three — use early returns and
  guard clauses
- No debug statements (`fmt.Println`, `log.Print` for debugging) in
  committed code; no commented-out code blocks
- Source files UTF-8, ASCII content only, LF line endings

### 2.3 Package and interface design

- `internal/` for all application code — external packages cannot
  import it
- Interfaces are owned by the caller, not the implementer:
  `ingest.Repository` is defined in `internal/ingest/`, not in the
  package that implements it
- Keep interfaces small — 1-3 methods; a large interface signals a
  design problem
- Accept interfaces, return concrete types
- Avoid package-level `init()` — use explicit initialisation in `main`
- Apply SOLID at the package and type level; prefer composition over
  inheritance and depend on abstractions, inject dependencies

### 2.4 Error handling

- Never discard errors — no `_` on an error return
- Wrap errors with context: `fmt.Errorf("flushing metrics: %w", err)`
- Use `errors.Is()` and `errors.As()` for inspection — never string
  matching
- Sentinel errors (`var ErrNoData = errors.New(...)`) defined in the
  package that owns the concept
- Log each error once, at the top of the call stack — not at every level
- Classify before handling — the class sets the response and log level:

| Class | Cause | HTTP | Log level |
| ------ | ------ | ------ | ------ |
| Validation | Invalid input from the caller | 400, 422 | INFO |
| Not found | Resource does not exist | 404 | INFO |
| Conflict | Duplicate or stale write | 409 | INFO |
| Infrastructure | DB, cache, or queue down | 503 | ERROR |
| Unexpected | Unhandled error, programming bug | 500 | ERROR |

- Never map an infrastructure or unexpected error to a 4xx, and never
  map a validation error to a 5xx
- Repository layer raises typed, domain-agnostic errors; service layer
  re-raises as domain errors with context; handler layer maps domain
  errors to HTTP via a central mapper — no ad-hoc `try`-style handling
  per route
- Wrap every outbound call (DB, cache) in a timeout — never wait
  indefinitely; treat every unexpected error as a bug and file a ticket

### 2.5 HTTP handlers

- Handlers are thin: decode request -> call service -> encode response;
  no business logic in handlers
- Decode the request body explicitly with `json.NewDecoder` and validate
  before use — never trust unvalidated input
- All error responses in JSON with an explicit
  `Content-Type: application/json`; follow a consistent shape and never
  return stack traces, internal paths, or driver errors to the client
- Path segments are lowercase plural nouns with hyphens
  (`/v1/metrics`) — no verbs, no trailing slash; query parameter names
  use camelCase, and `limit`, `skip`, `offset`, `expand`, `sortedBy`
  are reserved
- Date/time fields use ISO 8601; an integer above 2^53-1 is serialised
  as a string; reject non-finite floats (`NaN`/`Infinity`) at the
  encoder rather than emitting an invalid JSON token
- Use chi middleware for request ID injection, structured logging, and
  panic recovery — applied once at the router, not per route
- All traffic is served over HTTPS; write endpoints require an
  authenticated identity

### 2.6 Configuration

- One `Config` struct in `internal/config/config.go` — loaded from env
  vars at startup and passed explicitly through the dependency graph;
  no global config object
- Never read `os.Getenv` directly in application code outside the config
  loader
- Validate all required config at load time — `env.Parse` returns an
  error and the process fails fast if a required var is missing
- Env vars use `SCREAMING_SNAKE_CASE`, prefixed `METRICSTREAM_` to avoid
  collisions (e.g. `METRICSTREAM_DATABASE_URL`,
  `METRICSTREAM_REDIS_URL`, `METRICSTREAM_FLUSH_INTERVAL`)
- The port MUST be configurable via environment variable — never
  hardcoded
- `.env.example` committed with placeholders; `.env` in `.gitignore`;
  mark every secret as required with no default

### 2.7 Concurrency

- The flush worker runs as a goroutine started in `main.go` under an
  `errgroup` — never start a goroutine without a clear owner and a clear
  way to stop it
- `context.Context` is the first argument to every function that may
  block; propagate cancellation explicitly — never via package globals
- Protect the shared aggregation map with `sync.RWMutex` — document
  which fields the lock guards on the struct; never hold a lock across
  I/O
- Graceful shutdown: listen for `SIGTERM`, call HTTP server shutdown to
  drain in-flight requests, flush remaining buffered data, then cancel
  the root context
- Run tests with the race detector (`go test -race`) in CI — code review
  alone does not catch data races

### 2.8 Caching (Redis idempotency)

- Redis deduplicates ingest requests — store an idempotency key with a
  5-minute TTL; cache-aside on the receive path
- Key schema: `metricstream:ingest:<clientId>:<metricName>:<bucket>` —
  namespaced and documented; never built from unvalidated user input
- Every cache entry MUST have a TTL — no indefinite caching; size the
  TTL by acceptable staleness, not convenience
- Cache failures MUST NOT block ingestion — on miss or error, fall
  through to processing the request; log cache errors at WARN
- Never cache secrets, tokens, or PII; never cache at more than one layer
  for the same data
- Instrument cache hit rate, miss rate, and eviction rate; alert when
  hit rate drops well below baseline

### 2.9 Background jobs (flush worker)

- The periodic flush is a scheduled job defined in code (the worker
  interval is config-driven) — schedule-as-code, never configured
  manually in infrastructure
- The flush job MUST be idempotent — a re-run with the same buffered
  batch produces the same PostgreSQL state; design for at-least-once
- The job handler is thin — it delegates the aggregation-to-rows
  transform and the write to `flush.Repository`, reusing the same
  service path, with no parallel logic
- No direct ad-hoc database access outside the repository; no HTTP calls
  inside the flush job
- Retry a failed flush with exponential backoff and a bounded retry
  limit; on exhaustion, route the batch to a dead-letter store rather
  than dropping it, and alert on dead-letter depth
- Ensure only one flush instance runs per replica set — use a
  distributed lock or leader election so concurrent pods do not
  double-write
- Emit a structured INFO log at flush start and completion; log failures
  at ERROR with batch ID, attempt number, and error; track flush
  duration, buffer size, and failure rate as metrics

### 2.10 Database

- PostgreSQL via `pgx/v5` — use the connection pool, never a connection
  per request; inject the pool as a dependency, no global DB handle
- Parameterised queries only — never interpolate values into SQL strings
- No unbounded queries; avoid `SELECT *` — select only the columns
  needed
- Add an index for every foreign key and for the common
  filter-plus-sort combinations on the time-series table; use a partial
  index where a column is usually filtered the same way
- Wrap multi-step writes in a transaction and keep it short — never hold
  a transaction across the HTTP request boundary or call an external
  service inside one
- All schema changes via goose migrations — one migration per logical
  change, each reversible with a `down`; never edit a merged migration
- Tests reset state between runs and use real PostgreSQL — never
  substitute a different engine

## 3. Quality

### 3.1 Testing

- Stdlib `testing` package — no third-party assertion libraries
- Table-driven tests with `t.Run()` for parameterised cases
- Test the public API of each package — not unexported functions
- Inject dependencies via interfaces — no monkey-patching
- Component test naming: `Test<UnitOfWork>_<State>_<Expected>` —
  e.g. `TestIngestHandler_MalformedJSON_Returns400`
- Integration tests in `internal/<feature>/*_integration_test.go`
  behind `//go:build integration`; they use real PostgreSQL and Redis
  via Docker Compose (`make test-integration`)
- Test the cache fallback path: a cache miss or error still ingests
  correctly; test the flush retry and dead-letter paths
- New code MUST reach 90% coverage; total coverage MUST NOT regress and
  SHOULD stay at or above 80%
- Performance tests with k6 in `tests/performance/` — watch queue depth
  and flush lag at volume, not just receive latency
- Run before every commit: `go test -race ./... && go vet ./...`

### 3.2 Observability

- Structured JSON logs via `log/slog` (stdlib) — request ID in every log
  line; default level INFO, DEBUG/TRACE off in production
- Log each error once at the top of the call stack; 4xx at INFO, 5xx at
  ERROR; never log secrets, tokens, or PII
- `/health` — liveness, returns 200 if the process is alive; requires no
  authentication
- `/ready` — readiness, verifies PostgreSQL and Redis connectivity,
  returns 503 when a critical dependency is down
- Assign a trace ID at the service boundary, propagate it via the W3C
  `traceparent` header, and return it on errors (`Api-Trace-Id`)
- Instrument with OpenTelemetry; expose Prometheus metrics at `/metrics`
  with low-cardinality span names (route templates, not URLs with IDs):
  - `metricstream_ingest_requests_total` (by status)
  - `metricstream_flush_duration_seconds` (histogram)
  - `metricstream_aggregation_buffer_size` (gauge)

## 4. Identity

Not applicable — this project has no design system or brand voice. Its
public contract is the OpenAPI schema for `/v1/metrics`, maintained by
hand in `docs/openapi.yaml` and validated in CI.

## 5. Review process

### 5.1 Code review

Before merging, review the diff against the base branch in priority
order (highest first):

1. Security — no secrets or PII in logs, HTTPS-only, parameterised
   queries, write endpoints authenticated, container runs as non-root
2. Correctness — handlers thin, services framework-agnostic,
   aggregation map locked correctly, flush idempotent, cache failures
   non-fatal, transactions scoped and short, no N+1 queries
3. Clarity — names are self-documenting, functions single-purpose,
   cognitive complexity <= 15, exported symbols documented
4. Conventions — gofmt / go vet / staticcheck clean, interfaces owned by
   the caller, error wrapping and classification correct, URI and
   query-parameter casing rules

Confirm CI is green (build, lint, `go test -race`, govulncheck,
gitleaks). Only merge after the review passes.

### 5.2 Structure audit

- Run `go test -race ./... && go vet ./... && staticcheck ./...` before
  every PR
- Verify `.env.example` lists every required variable and `README.md`
  documents the env reference and Makefile targets
- Verify every new endpoint has success / 4xx / auth tests and that the
  flush and cache paths have integration coverage
- Confirm each schema change has a reversible goose migration committed
- Run the audit after: new project, migration, a new feature package, or
  before a release

## 6. Session protocol

### 6.1 Start of session

1. Read this `CLAUDE.md` and `README.md` in full before the first change
2. Check the current branch — if not `main`, ask why before proceeding
3. Check `git status` — if uncommitted changes exist, ship the previous
   session's wrap (branch, commit, push, merge) before any new work
4. Clean up stale branches: `git fetch --prune`, then delete local
   branches whose PRs have merged
5. Check the latest CI/CD deploy on `main` completed successfully — flag
   if stuck, failed, or pending
6. Confirm the scope with the user before making changes
7. If the task is ambiguous, ask: "What is the specific deliverable for
   this session?"
8. Review open issues related to the agreed scope before writing code

### 6.2 During the session

- Flag explicitly when a task grows beyond the agreed scope — do not
  silently absorb new requests
- Finishing and committing the current work takes priority over starting
  something new
- Run `go test -race ./... && go vet ./...` after every change — do not
  accumulate unverified changes
- When a tool (goimports, golangci-lint, goose autogenerate) touches
  unrelated files, revert the drift before committing and file it
  separately

### 6.3 End of session

When the user signals end of session ("wrap up", "let's finish", "end
session", "close out", or similar), print the full checklist below and
execute each item sequentially. Mark each item done (with result) before
moving to the next. Do not batch, skip, or summarize — visible
sequential execution prevents missed steps.

1. Commits and push — all changes committed and pushed (via PR if
   branch-protected)
2. Close issues — close completed issues (verify auto-close worked)
3. Epic checklists — update epic checklists if relevant
4. Dev journal — add a session entry to `docs/dev-journal.md` (date,
   tool, key changes, PRs merged, issues closed/created)
5. ADRs — record any architectural decisions in `docs/decisions/`; a new
   directory or content move between documents each needs an ADR
6. Migrations — confirm every schema change has a reversible goose
   migration committed and applied (`make migrate-up`)
7. CLAUDE.md — for each new convention, decide whether it belongs here
   (a rule the agent MUST apply every turn) or in another doc; keep each
   rule to one line
8. README.md — for each new command, dependency, or env var, confirm it
   is reflected; name the section
9. docs/ONBOARDING.md — for each new tool, prerequisite, or setup step,
   confirm it is documented; name the section
10. docs/PLAYBOOK.md — for each new command, script, or workflow,
    confirm it is documented; name the section
11. Tests and analysis — run `go test -race ./... && go vet ./... &&
    staticcheck ./...` and confirm all pass
12. Flag gaps — if any item cannot be completed this session, report it
    as pending (never as done) before closing
13. Summary — summarize what was done and what is next
