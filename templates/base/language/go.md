# Base — Go
[ID: base-go]
[DEPENDS ON: templates/base/core/quality.md]

Per-language tool selection for Go. `base-quality-gates` states which
categories a project MUST gate and at which layer; this file names the Go
tool that satisfies each. Stack templates add only the tools their shape
changes and do not re-declare the bindings below.

## Tooling
[ID: base-go-tooling]

| Category              | Tool                          | Config                    |
| --------------------- | ----------------------------- | ------------------------- |
| Commit-hook framework | `pre-commit`                  | `.pre-commit-config.yaml` |
| Lint                  | `golangci-lint`               | `.golangci.yml`           |
| Format                | `gofmt`                       | built-in                  |
| Type check            | `go vet`                      | —                         |
| Cognitive complexity  | `gocognit` via `golangci-lint`| `.golangci.yml`           |
| Security (SAST)       | `govulncheck`                 | —                         |
| Tests                 | `go test`                     | —                         |
| Coverage              | `go test -cover`              | —                         |
| Package manifest      | `go.mod`                      | —                         |

- Cognitive complexity binds through `golangci-lint` rather than a
  separate binary — `gocognit` ships as one of its linters, so the gate
  needs a config entry rather than another dependency
- `gocognit` MUST be named explicitly in `.golangci.yml`. It is not in
  the default linter set, so a config that omits it runs no complexity
  check at all while the lint gate still reports success — the gate
  passes because it measured nothing
- Prefer `gocognit` over `gocyclo`. `gocyclo` is a McCabe branch count,
  which `quality-gates-complexity` states is the metric a readability
  standard is not after
- `gofmt` settles formatting; Go projects MUST NOT carry a formatter
  choice or a style config. Its output is canonical, which is why the
  Format category needs no options here
