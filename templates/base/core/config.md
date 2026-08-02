# Base — Configuration
[ID: base-config]

Follows the [12-factor app](https://12factor.net/config) principle:
store config in the environment, not in code.

## Rules

- All configuration from environment variables — no hardcoded values
  in source
- Never hardcode secrets, API keys, or credentials — environment only
- `.env.example` committed with placeholder values; `.env` in
  `.gitignore`
- Separate configuration per environment (development, testing,
  production)
- Pass config explicitly to components — no global config objects
  accessed from arbitrary locations
- Validate all required config at load time — fail fast if anything
  is missing or invalid

## Naming conventions

- Use `SCREAMING_SNAKE_CASE` for all environment variables
- Prefix with the app or service name to avoid collisions
  (e.g. `MYAPP_DATABASE_URL`, not `DATABASE_URL`)
- Group related variables with a common prefix
  (e.g. `MYAPP_DB_HOST`, `MYAPP_DB_PORT`, `MYAPP_DB_NAME`)
- Boolean variables use `ENABLE_` or `DISABLE_` prefix
  (e.g. `MYAPP_ENABLE_CACHE`)

## Config precedence

Sources override in this order (highest wins):

1. **Hardcoded defaults** — in code, lowest priority
2. **Config file** — `config.yaml`, `appsettings.json`, etc.
3. **Environment variables** — override file values
4. **CLI flags / arguments** — override everything

- Document the precedence model for the project
- Never let a lower-priority source silently override a
  higher-priority one

## In-process config model

For a library or CLI whose run configuration is an in-process object
with named presets — build profiles, dataset variants, run modes — not
an environment, model it explicitly instead of re-declaring the same
inputs inside each command. This composes with 12-factor: env vars wire
deployment and secrets; the in-process object holds one run's inputs.

- **Frozen object** — bundle all inputs for one run in an immutable
  record (frozen dataclass, readonly struct); each default carries its
  rationale in place, so a preset's diff reads as intent
- **Registry** — map names (and aliases) to instances; look up
  case-insensitively and raise on a miss, listing the known keys
- **Unset-means-default resolution** — CLI flags default to a
  null/sentinel, and a shared resolver backfills each unset field from
  the selected preset while an explicit value always wins. This
  separates "user said nothing" from "user said this" — never default a
  flag to the preset value directly, or the two become indistinguishable
- **Derive layout from the object** — compute paths as properties
  (e.g. `out_dir` from the run name) so nothing hardcodes them; a copy
  accessor hands callers a mutable copy so they cannot mutate the shared
  frozen object
- **Serialisable record** — give the object `to_dict` / `from_dict`
  (plus `load` / `save`), keyed by field name. `from_dict` does
  structural validation only — required keys, types, reject unknown
  keys so a typo fails loud — which keeps deserialising cheap and
  dependency-light
- **One resolver, two sources** — the same selector that names a
  built-in MUST also accept a user-supplied config file, so an
  installed tool runs a user's own configuration without editing
  source. The resolver grows one branch: a value carrying an explicit
  file marker (an extension or a path separator) loads the file; a bare
  word stays the registry lookup, byte-identical. Never branch on
  `exists()` — a bare registry key would then collide with a
  same-named file in the working directory
- **Ad-hoc flags are sugar over the file path** — a second front door
  materialises a file and delegates to it, so construction and
  validation keep one path and the ad-hoc run leaves behind a
  reproducible artifact
- **Validate at the door** — check a user config against the supported
  envelope on entry, reporting a message that names the supported set
  rather than a traceback deep in the run. Separate the cheap
  always-on checks (name safety, enum membership) from the expensive
  ones that need a heavy import, so a dry run stays cheap

## Build-time vs runtime config

- **Build-time** — values baked into the artifact at build (API base
  URLs, feature flags, public keys). Changing them requires a rebuild.
- **Runtime** — values read when the process starts or on each
  request (secrets, database URLs, log levels). Changing them
  requires a restart or hot-reload.
- Never put secrets in build-time config — they end up in the
  artifact and are visible to anyone who inspects it
- Document which variables are build-time and which are runtime

## Validation

- Validate types, ranges, and formats at load time — not at first use
- Use a typed config object or schema — never scatter raw environment
  variable reads across the codebase
- Provide sensible defaults only for optional, non-sensitive settings
- Mark all secrets as required — no defaults for passwords, tokens,
  or keys

## Secrets management

- In production, source secrets from a dedicated secrets manager or
  CI/CD secret store — not from flat `.env` files
- Design secret loading to support rotation without a full
  redeployment
- Never log config values — redact or omit secrets from logs and
  diagnostic output
- Reference secrets by name or path, not by embedding them in config
  files

## Environment separation

| Environment | Purpose           | Secrets source       |
|-------------|-------------------|----------------------|
| development | local work        | `.env` file          |
| testing     | automated tests   | hardcoded stubs      |
| staging     | pre-production    | secrets manager / CI |
| production  | live              | secrets manager      |

## Dependencies

- Declare all dependencies explicitly in a manifest (`package.json`,
  `pyproject.toml`, `go.mod`, `Cargo.toml`, `requirements.txt`)
- Commit the lockfile (`package-lock.json`, `poetry.lock`, `go.sum`,
  `Cargo.lock`) — it pins exact versions for reproducible builds
- Never rely on system-wide packages — the app MUST run with only
  its declared dependencies installed
- Separate production dependencies from dev/test dependencies
- When an updater splits interlocked packages (caret-ranged pairs like
  `react`/`react-dom` or an ESLint plugin/parser) into separate PRs,
  rebase the co-dependent PRs against current `main` before merging the
  second — or group them in `.github/dependabot.yml` (`groups`) so they
  ship as one PR. Each passes CI alone, yet a lone merge can leave the
  lockfile with mismatched pins

## Port binding

- The application exposes its service by binding to a port — it does
  not depend on an external web server injecting itself at runtime
- The port MUST be configurable via environment variable
  (e.g. `PORT=8080`)
- Do not hardcode port numbers in source code
- In development, use a well-known default; in production, the
  platform assigns the port

## `.env.example` structure

```
# Required
API_BASE_URL=http://localhost:8000
SECRET_KEY=change-me

# Optional — defaults shown
LOG_LEVEL=info
DEBUG=false
```
