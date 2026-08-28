# Stack — Go Library / CLI
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/language/go.md, templates/base/core/cli.md, templates/base/core/testing.md, templates/base/workflow/quality-gates.md, templates/base/core/examples.md]

Base Go conventions for any Go module — library, CLI tool, or service.
Never used directly for services — always extended by
`templates/stack/go-service.md`.
Can be used directly for pure Go libraries or standalone CLI tools with
no HTTP layer.

---

## Stack
[ID: go-lib-stack]

- Language: Go 1.22+
- CLI framework: [cobra / flag (stdlib)] — only for command packages
- Test runner: go test (stdlib)
- Distribution: [binary / GitHub Releases / Go module proxy]

---

## Package and interface design
[ID: go-lib-packages]

- Small, focused packages — one domain concern per package
- Define interfaces where the caller, not the implementer, owns them
- Keep interfaces small: prefer 1–3 methods
- Accept interfaces, return concrete types (in most cases)
- Avoid package-level `init()` — use explicit initialisation in `main`
- No `utils/` or `helpers/` packages — name packages by domain

---

## Error handling
[ID: go-lib-errors]

- Always handle errors — never `_` discard an error return
- Wrap errors with context: `fmt.Errorf("creating user: %w", err)`
- Use `errors.Is()` and `errors.As()` for inspection — never string matching
- Define sentinel errors (`var ErrNotFound = errors.New(...)`) in the package
  that owns the concept

---

## Go conventions
[ID: go-lib-conventions]
[EXTEND: base-quality]

- Follow **Effective Go** (https://go.dev/doc/effective_go) for idioms and
  design decisions — the canonical Go style reference
- Follow **Go Code Review Comments** (https://go.dev/wiki/CodeReviewComments)
  for common pitfalls and reviewer expectations
- `gofmt` / `goimports` — code must be formatted; CI rejects unformatted code
- Run `go vet ./...` — fix all warnings before committing
- Run `staticcheck ./...` for additional static analysis
- No unused imports or variables — the compiler rejects these
- Exported symbols must have a doc comment

---

## Testing
[ID: go-lib-testing]
[EXTEND: base-testing]

- Use stdlib `testing` package — no third-party assertion libraries
- Table-driven tests with `t.Run()` for parameterised cases
- Test the public API of each package — not unexported functions
- Use interfaces to inject dependencies in tests — no monkey-patching
- Component test naming: `Test<UnitOfWork>_<State>_<Expected>`
  e.g. `TestParseConfig_MissingField_ReturnsError`
- Run before every commit: `go test ./... && go vet ./...`

---

## Examples
[ID: go-lib-examples]
[EXTEND: base-examples]

- Prefer `Example` functions in `_test.go` with an `// Output:` comment.
  `go test` compares the comment against what the function prints, so
  the real-output rule is machine-checked rather than reviewed, and the
  example cannot rot silently
- Reach for a standalone `examples/` directory only for what an
  `Example` function cannot carry — a multi-file program, a CLI
  invocation, a flag-driven journey
- Each program under `examples/` MUST be `package main`, so it cannot
  be imported as library API and cannot widen the module's surface
- Smoke check: `go vet ./... && go test ./...` covers the `Example`
  functions; `go run ./examples/<name>` covers the directory. Pass
  condition — every program exits zero

---

## Git conventions
[ID: go-lib-git]
[EXTEND: base-git]

- Do not commit compiled binaries or `*.test` files
- Do not commit `vendor/` unless vendoring is an explicit project decision —
  document it in README if so
- `go.sum` is committed — do not delete or regenerate without cause
- Tag releases with `vX.Y.Z` — Go module proxy uses these

---

## Commands
```
go build ./...        # compile all packages
go test ./...         # run all tests
go vet ./...          # static analysis
goimports -w .        # format imports
staticcheck ./...     # additional static analysis
```
---

## Quality gates
[EXTEND: base-quality-gates]

`base-go-tooling` names the tool for every category Go binds. This
section adds only what the module shape changes, and the tools that are
not language-specific.

| Category | Layer 1 (editor) | Layer 2 (pre-commit) | Layer 3 (CI) |
| -------- | ---------------- | -------------------- | ------------ |
| Secrets  | —                | gitleaks             | gitleaks     |

- Secret detection is not language-specific, so it binds here rather than
  in `base-go`: `gitleaks`, configured in `.pre-commit-config.yaml`
- The SAST scanner `base-go` binds runs alongside the hosted analysis the
  platform template supplies; neither replaces the other, and a platform
  that supplies none leaves the local scanner as the whole gate
- Hook framework: `pre-commit` or Makefile
