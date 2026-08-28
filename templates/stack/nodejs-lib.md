# Stack — Node.js Library / CLI
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/language/typescript.md, templates/base/core/cli.md, templates/base/core/examples.md]

A Node.js library or CLI tool written in TypeScript. Intended to be
published to npm or used as a shared internal package. No web server,
no frontend. Covers package structure, exports, CLI conventions,
versioning, and testing.

---

## Stack
[ID: nodejs-lib-stack]

- Language: TypeScript (strict mode)
- Runtime: Node.js 20+ (LTS)
- Package manager: [npm / pnpm]
- Build tool: [tsup / tsc / esbuild]
- Linter: ESLint (`@typescript-eslint/recommended`, `eslint-plugin-sonarjs`)
- Formatter: Prettier
- Test runner: Vitest
- Distribution: [npm (public) / npm (private) / GitHub Packages]

---

## Project structure
[ID: nodejs-lib-structure]

```
src/
  index.ts                   # public API — re-exports only; no logic here
  [module].ts                # one file per logical concern
  cli.ts                     # CLI entry point (if applicable)
  types.ts                   # shared TypeScript types and interfaces
tests/
  [module].test.ts
examples/
  README.md                  # index — command and real output per example
  [pattern].mjs              # runnable against the built package
dist/                        # build output — gitignored
tsconfig.json
tsconfig.build.json          # excludes tests from the build output
package.json
.eslintrc.json
.prettierrc
README.md
CLAUDE.md
```

---

## TypeScript conventions
[ID: nodejs-lib-typescript]
[EXTEND: base-typescript]

- `tsconfig.build.json` excludes `tests/` — type-check tests separately

---

## Package exports
[ID: nodejs-lib-exports]

- Use the `exports` field in `package.json` for all entry points —
  do not rely on `main` alone for modern Node.js consumers
- Dual CJS + ESM output if broad compatibility is required; ESM-only
  is acceptable for Node.js 20+ targets
- `types` or `typesVersions` field pointing to generated `.d.ts` files —
  consumers must get types without extra configuration
- Mark the package `"sideEffects": false` if it has none — enables
  tree-shaking in bundlers
- Never expose internal modules in `exports` — only the intended public API

```json
"exports": {
  ".": {
    "import": "./dist/index.mjs",
    "require": "./dist/index.cjs",
    "types": "./dist/index.d.ts"
  }
}
```

---

## CLI conventions (if applicable)
[ID: nodejs-lib-cli]

- Entry point in `src/cli.ts` — wired to `bin` in `package.json`
- Parse arguments with [commander / yargs / citty] — never `process.argv`
  directly
- Exit codes: `0` for success, `1` for user error, `2` for internal error
- Write output to `stdout`; write errors and logs to `stderr`
- Support `--help` and `--version` flags — both generated automatically
  by the chosen argument parser
- Never call `process.exit()` in library code — only in the CLI entry point
- `npx`-compatible: the package must work without a global install

---

## Code conventions
[ID: nodejs-lib-conventions]

- Pure functions where possible — no hidden side effects
- Raise specific error types that extend `Error` — never throw plain strings
- No global mutable state — callers create instances or pass config explicitly
- All async functions return `Promise` — no callbacks in public API
- Log to `stderr` only if the library is a CLI tool; library code must
  never write to stdout/stderr without explicit opt-in by the caller

---

## Testing
[EXTEND: base-testing]

- Vitest for all tests — fast, TypeScript-native, no separate config needed
- Aim for 100% coverage of the public API
- No mocks for pure functions — test with real inputs
- Mock only at external boundaries (file system, network, process)
  using `vi.mock()` or a dependency injection pattern
- Component test naming: `<function>_<state>_<expected>`
  e.g. `parseConfig_missingRequiredField_throwsValidationError`
- Run before every commit: `npm test && tsc --noEmit`

---

## Examples
[ID: nodejs-lib-examples]
[EXTEND: base-examples]

- Examples MUST run against the built package, not raw TypeScript. A
  consumer who installed from npm has no `tsx` or `ts-node`, so an
  example written in `.ts` is unrunnable for the reader it is written
  for. Ship `.mjs` importing the package by name, or compile the
  examples in the smoke job before running them
- `examples/` MUST be excluded from the published package. The `files`
  field in `package.json` is an allowlist — a directory absent from it
  is already excluded, and `npm pack --dry-run` lists what would ship
- Smoke check: pack and install the tarball into a clean directory —
  `npm pack`, then `npm install <tarball>` — and run each example
  against it. Installing the workspace with `--omit=dev` is the weaker
  form: it proves the example runs beside the source tree, not against
  what npm serves

---

## Versioning and publishing
[ID: nodejs-lib-publishing]

- Semantic versioning — `MAJOR.MINOR.PATCH` per semver.org
- `CHANGELOG.md` updated on every release — use Conventional Commits
  to automate with `release-it` or `changesets`
- Publish to npm from CI only — never from a local machine
- Use `npm publish --dry-run` in CI on PRs to catch packaging errors early
- Tag releases `vX.Y.Z` in git before publishing

---

## Git conventions
[EXTEND: base-git]

- Do not commit `node_modules/`, `dist/`
- Lock file (`package-lock.json` / `pnpm-lock.yaml`) is committed
- `dist/` excluded from git but included in the npm package via
  `files` field in `package.json`

---

## Commands
```
npm run build        # compile TypeScript → dist/ (via tsup or tsc)
npm test             # run Vitest tests
npm run lint         # ESLint
npm run format       # Prettier
tsc --noEmit         # type check without building
npm publish --dry-run  # verify package contents before publishing
npm publish          # publish to npm (CI only)
```