# Stack — NestJS Application
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/language/typescript.md, templates/base/core/config.md, templates/backend/http.md, templates/backend/api.md, templates/backend/database.md, templates/backend/observability.md, templates/backend/auth.md, templates/backend/quality.md, templates/backend/features.md, templates/backend/messaging.md, templates/base/infra/cicd.md, templates/base/security/devsecops.md]

A Node.js backend built with NestJS. Covers modules, controllers, providers,
dependency injection, guards, pipes, interceptors, database integration,
and testing.

---

## Stack
[ID: nestjs-stack]

- Language: TypeScript (strict mode)
- Framework: NestJS 10+
- Runtime: Node.js 20+ (LTS)
- HTTP adapter: [Express (default) / Fastify]
- Validation: class-validator + class-transformer
- ORM: [TypeORM / Prisma / MikroORM]
- Package manager: [npm / pnpm]
- Linter: ESLint (`@typescript-eslint/recommended`, `eslint-plugin-sonarjs`)
- Formatter: Prettier
- Test runner: Jest + Supertest
- Process manager (production): PM2 or Docker
- Distribution: Docker image / [platform]

---

## Project structure
[ID: nestjs-structure]

```
src/
  [feature]/
    [feature].module.ts      # module definition
    [feature].controller.ts  # HTTP handlers (thin)
    [feature].service.ts     # business logic
    [feature].repository.ts  # data access (if not using ORM repositories directly)
    dto/
      create-[feature].dto.ts
      update-[feature].dto.ts
    entities/
      [feature].entity.ts
    [feature].controller.spec.ts
    [feature].service.spec.ts
  common/
    filters/                 # exception filters
    guards/                  # auth guards
    interceptors/            # logging, transform interceptors
    pipes/                   # validation pipes
    decorators/              # custom decorators
  config/
    configuration.ts         # typed config via @nestjs/config
  app.module.ts              # root module
  main.ts                    # bootstrap
test/
  [feature].e2e-spec.ts
tsconfig.json
tsconfig.build.json
nest-cli.json
package.json
.env.example
Dockerfile
README.md
CLAUDE.md
```

---

## Modules
[ID: nestjs-modules]

- One module per feature domain — `@Module({ imports, controllers, providers,
  exports })`
- Modules are self-contained: controller, service, repository, DTOs, and
  entities live inside the feature directory
- Export only what other modules genuinely need — favour encapsulation
- `AppModule` imports feature modules — no business logic in `AppModule`
- `ConfigModule.forRoot({ isGlobal: true })` registered once in `AppModule`

---

## Controllers
[ID: nestjs-controllers]

- Thin — decode input, delegate to service, return response
- One controller per resource with a route prefix: `@Controller('users')`
- Use `@Get()`, `@Post()`, `@Put()`, `@Patch()`, `@Delete()` decorators —
  one method per operation
- Validate all input via `@Body()`, `@Param()`, `@Query()` with DTO classes
  and the global `ValidationPipe`
- Never put business logic in a controller — delegate to the service

---

## Services and providers
[ID: nestjs-services]

- Business logic lives in `@Injectable()` services
- Services are the only layer that accesses repositories or external APIs
- One service per feature — split if a service grows beyond one domain concern
- Constructor injection via NestJS DI — never use `new` to instantiate services

---

## Validation
[ID: nestjs-validation]

- Enable `ValidationPipe` globally in `main.ts`:
  `whitelist: true, forbidNonWhitelisted: true, transform: true`
- All request bodies typed with DTO classes decorated with `class-validator`
  decorators (`@IsString()`, `@IsInt()`, `@IsEmail()`, etc.)
- `transform: true` enables automatic type coercion — keep DTO types explicit
- Never pass raw `req.body` to a service — always go through a validated DTO

---

## Cross-cutting concerns
[OVERRIDE: base-oop-aop]

NestJS uses framework-managed interceptors, guards, pipes, and filters as
its standard cross-cutting model. These are explicit, typed, and visible in
the module wiring — not hidden AOP proxies.

- Use guards for auth, interceptors for logging/transform, pipes for
  validation, and exception filters for error handling
- Register cross-cutting providers at the module or global level — never
  via hidden runtime proxies or bytecode weaving
- Each provider has a single responsibility — do not combine auth and
  logging in one interceptor

## Guards and interceptors
[ID: nestjs-guards]

- Auth guard (`JwtAuthGuard` or equivalent) applied globally or per controller —
  opt out with `@Public()` decorator on public endpoints
- Authorization (role/permission checks) in a separate `RolesGuard` —
  never mix authn and authz in one guard
- Logging interceptor at the global level — logs request ID, method, path,
  duration, and status code
- Transform interceptor for consistent response envelope (if required by API
  contract)

---

## Configuration
[EXTEND: base-config]

- Use `@nestjs/config` with a typed `configuration.ts` factory function
- Inject `ConfigService` via DI — never read `process.env` directly in
  application code
- Validate config at startup with Joi or class-validator schema

---

## Database (if applicable)
[EXTEND: backend-database]

- TypeORM: use `Repository<Entity>` injected via `@InjectRepository()`
- Prisma: use `PrismaService` as an injectable provider wrapping `PrismaClient`
- Migrations managed by the ORM CLI

---

## Feature flags (if applicable)
[EXTEND: backend-features]

- Inject the flag client as an `@Injectable()` provider
- Evaluate flags in the service layer — not deep inside domain logic or
  repositories

---

## Messaging (if applicable)
[EXTEND: backend-messaging]

- Use `@nestjs/microservices` for broker integration (Kafka, RabbitMQ, Redis)
- Define message handlers with `@MessagePattern()` or `@EventPattern()`
- Keep message handlers thin — delegate to the same service layer used by HTTP
  controllers

---

## Testing
[EXTEND: base-testing]

- Unit tests with Jest: test each service in isolation using
  `Test.createTestingModule()`
  with mocked dependencies
- Integration/e2e tests with Supertest: spin up the full NestJS app against
  a test database — test each endpoint for success, validation error, and auth
  error
- No mocking of the database in e2e tests — use a real test database
- Component test naming: `<method> <resource> <state> returns <expected>`
  e.g. `POST /users with duplicate email returns 409`
- Run before every commit: `npm test && npm run test:e2e && tsc --noEmit`

---

## Git conventions
[EXTEND: base-git]

- Do not commit `node_modules/`, `dist/`, `.env`
- Lock file committed — do not delete it
- Migrations are committed — never regenerate a migration already merged

---

## Commands
```
npm run start:dev          # develop — hot reload
npm run build              # compile TypeScript → dist/
npm run start:prod         # production server
npm run test               # unit tests
npm run test:e2e           # end-to-end tests
npm run test:cov           # coverage report
tsc --noEmit               # type check without building
```