# Base — C
[ID: base-c]
[DEPENDS ON: templates/base/core/quality.md]

Per-language tool selection for C. The categories a project gates are
the same for every language; this file names the C tool that satisfies
each. Stack templates add only the tools their shape changes — an
embedded stack's cross-compiled target, its host-side test runner — and
do not re-declare the bindings below.

## Tooling
[ID: base-c-tooling]

| Category              | Tool                                                    | Config                    |
| --------------------- | ------------------------------------------------------- | ------------------------- |
| Commit-hook framework | `pre-commit`                                            | `.pre-commit-config.yaml` |
| Lint                  | `clang-tidy`                                            | `.clang-tidy`             |
| Format                | `clang-format`                                          | `.clang-format`           |
| Type check            | the compiler, `-Wall -Wextra -Wconversion -Werror`      | `CMakeLists.txt`          |
| Cognitive complexity  | `readability-function-cognitive-complexity` via `clang-tidy` | `.clang-tidy`        |
| Security (SAST)       | `cppcheck`                                              | `compile_commands.json`   |
| Tests                 | `ctest`                                                 | `CMakeLists.txt`          |
| Coverage              | `gcovr` over `gcov` data                                | `gcovr.cfg`               |
| Mutation testing      | `mull`                                                  | `mull.yml`                |
| Package manifest      | `CMakeLists.txt`                                        | —                         |

- Cognitive complexity binds through `clang-tidy` rather than a separate
  binary — `readability-function-cognitive-complexity` ships as one of
  its checks, so the gate needs a config entry rather than another
  dependency
- The check MUST be named explicitly in `.clang-tidy`. It is not in the
  default check set, so a config that omits it runs no complexity check
  at all while the lint gate still reports success — the gate passes
  because it measured nothing. Its threshold option carries the number
  `base-quality` states
- Prefer it over a cyclomatic tool. `lizard`, `pmccabe` and `clang-tidy`'s
  own `readability-function-size` count branches, which is McCabe — a
  different metric from the one a readability bar is after
- C has no type checker apart from the compiler, so the Type check gate
  is warnings as errors. A warning the build lets through is a type
  error the build accepted; `-Wconversion` is the one the default sets
  omit and the one that catches a narrowing an embedded target cannot
  afford
- `clang-format` MUST read a committed `.clang-format` naming a
  `BasedOnStyle`. The tool's default style differs between versions, so
  a project carrying no file is formatted by whichever version each
  contributor has installed
- `cppcheck` MUST run against the build's `compile_commands.json`
  (`--project=`), never against a source directory alone. Run over
  `src/` it analyses code the build never compiles and misses every
  branch behind a define the toolchain sets
- The coverage tool is named here; the threshold is not. The number and
  its escalation policy are project configuration, the same for every
  language
- Mutation testing is opt-in, and a project that has not adopted it
  carries no `mull.yml`
