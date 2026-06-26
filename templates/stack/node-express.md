# Stack — Express.js Application
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/language/typescript.md, templates/base/core/config.md, templates/backend/http.md, templates/backend/api.md, templates/backend/database.md, templates/backend/observability.md, templates/backend/auth.md, templates/backend/quality.md, templates/backend/features.md, templates/backend/messaging.md, templates/base/infra/cicd.md, templates/base/security/devsecops.md]

A Node.js REST API built with Express. Covers project structure, middleware,
routing, validation, error handling, and testing. Express is unopinionated —
these conventions fill the gap.

---

## Stack
[ID: express-stack]

- Language: TypeScript (strict mode)
- Framework: Express 4+ / 5+
- Runtime: Node.js 20+ (LTS)
- Validation: [Zod / joi / express-validator]
- ORM / query builder: [Prisma / Drizzle / Knex / pg]
- Package manager: [npm / pnpm]
- Linter: ESLint (`@typescript-eslint/recommended`, `eslint-plugin-sonarjs`)
- Formatter: Prettier
- Test runner: Vitest + Supertest
- Production server: Node.js process managed by PM2 or Docker
- Distribution: Docker image / [platform]

---

## Project structure
[ID: express-structure]

```
src/
  [feature]/
    [feature].router.ts      # Express Router — thin, delegates to service
    [feature].service.ts     # business logic
    [feature].repository.ts  # data access
    [feature].schema.ts      # Zod schemas for request validation
    [feature].types.ts       # TypeScript types for this domain
  middleware/
    auth.ts                  # JWT verification middleware
    requestId.ts             # attach unique ID to every request
    errorHandler.ts          # global error handler
    validate.ts              # reusable validation middleware factory
  config/
    index.ts                 # typed config loaded from env vars
  db/
    client.ts                # database client / Prisma client singleton
  app.ts                     # Express app setup — middleware, routers
  server.ts                  # HTTP server bootstrap (listen, graceful shutdown)
tests/
  [feature].test.ts
tsconfig.json
package.json
.env.example
Dockerfile
README.md
CLAUDE.md
```

---

## Application setup
[ID: express-app]

- Separate `app.ts` (Express app) from `server.ts` (HTTP server) —
  `app.ts` is imported in tests without starting the server
- Register middleware in order: request ID → body parser → auth → routes →
  not-found handler → error handler
- No business logic in `app.ts` — only middleware and router registration
- Graceful shutdown: listen for `SIGTERM`, drain in-flight requests, then exit

---

## Routing
[ID: express-routing]

- One `Router` per feature domain — mounted in `app.ts` with a path prefix
- Route handlers are thin: validate input, call service, send response
- Never put database calls or business logic in a route handler
- All routes typed with explicit `Request<Params, ResBody, ReqBody, Query>`
  generics from `@types/express`

---

## Validation
[ID: express-validation]

- Validate all incoming data (body, params, query) with a schema before the
  handler runs — use a `validate(schema)` middleware factory
- Use Zod: define a schema in `[feature].schema.ts`, call `schema.parse()`
  or `schema.safeParse()` — never trust unvalidated input in a service
- Return 400 with a structured error body on validation failure —
  follow RFC 9457 format (per `templates/backend/http.md`)

---

## Error handling
[ID: express-errors]

- One global error handler registered last in `app.ts`:
  `app.use((err, req, res, next) => { ... })`
- All async route handlers wrapped with a `asyncHandler` utility that
  catches rejected promises and forwards to `next(err)` —
  never use `try/catch` in every handler individually
- Typed error classes (e.g. `NotFoundError`, `ValidationError`) extend a
  base `AppError` with `statusCode` — the global handler maps these to
  HTTP responses
- Never expose stack traces in production responses

---

## Configuration
[EXTEND: base-config]

- All config in `src/config/index.ts` as a typed object parsed from env vars
  using Zod or `envalid` — fail fast if required vars are missing
- Import the config object; never read `process.env` directly in application
  code

---

## Database (if applicable)
[EXTEND: backend-database]

- Prisma: instantiate `PrismaClient` once in `src/db/client.ts`, import
  where needed — never create multiple instances
- Knex / Drizzle: single connection pool created at startup, passed through
  the dependency graph — no module-level globals in feature code
- Migrations managed by the chosen tool's CLI

---

## Feature flags (if applicable)
[EXTEND: backend-features]

- Instantiate the flag client once at startup and attach to `app.locals`
  or pass through the dependency graph — never re-initialise per request

---

## Messaging (if applicable)
[EXTEND: backend-messaging]

- Consumer processes run separately from the Express HTTP server —
  a single Node.js process should not handle both HTTP and long-running
  broker connections unless resource constraints require it
- Use `bullmq` (Redis-backed) for job queues within the same deployment unit

---

## Testing
[EXTEND: base-testing]

- Supertest for HTTP-level tests — import `app` directly, no server listen
  needed
- Vitest for unit tests on services, repositories, and utilities
- No mocking of the database in integration tests — use a real test database
- Test each route for: success (2xx), validation error (400), auth error
  (401/403)
- Component test naming: `<METHOD> <path> <state> returns <status>`
  e.g. `POST /users with duplicate email returns 409`
- Run before every commit: `npm test && tsc --noEmit`

---

## Git conventions
[EXTEND: base-git]

- Do not commit `node_modules/`, `dist/`, `.env`
- Lock file committed — do not delete it

---

## Commands
```
npm run dev          # develop — hot reload (ts-node-dev or tsx watch)
npm run build        # compile TypeScript → dist/
npm run start        # production server (node dist/server.js)
npm test             # run tests (Vitest)
tsc --noEmit         # type check without building
```