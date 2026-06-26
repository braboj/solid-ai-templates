# Stack — Rust Library / CLI
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md]

A Rust library crate, binary crate, or CLI tool. Covers crate structure,
ownership and error handling idioms, async conventions, testing, and
publishing to crates.io.

---

## Stack
[ID: rust-lib-stack]

- Language: Rust (stable channel, latest stable)
- Build tool: Cargo
- Async runtime: [Tokio / async-std / none] — only if async is needed
- Error handling: `thiserror` (libraries) / `anyhow` (binaries and CLIs)
- CLI argument parsing: [clap / argh] — only for binary crates
- Linter: `clippy` (stable + `clippy::pedantic` selectively)
- Formatter: `rustfmt`
- Test runner: Cargo built-in (`cargo test`)
- Distribution: [crates.io / GitHub Releases / binary download]

---

## Project structure
[ID: rust-lib-structure]

```
src/
  lib.rs                     # library root — public API and module declarations
  [module]/
    mod.rs                   # or [module].rs for single-file modules
  bin/
    [cli_name].rs            # binary entry point (if applicable)
  error.rs                   # error types
tests/
  [integration_test].rs      # integration tests — compiled as separate crates
benches/
  [bench].rs                 # criterion benchmarks (if applicable)
examples/
  [example].rs               # runnable examples documenting the public API
Cargo.toml
Cargo.lock                   # committed for binaries; gitignored for libraries
rustfmt.toml
.clippy.toml
README.md
CLAUDE.md
```

---

## Crate conventions
[ID: rust-lib-crate]

- `Cargo.toml`: set `edition = "2021"`, explicit `rust-version` minimum,
  `description`, `license`, `repository`, and `keywords` for all published crates
- `Cargo.lock`: committed for binary crates and applications; gitignored
  for library crates (let dependents resolve versions)
- Feature flags for optional dependencies — never unconditionally pull in
  heavy dependencies; gate them behind a `[features]` entry
- Keep the public API surface minimal — mark items `pub` only when callers
  genuinely need them; prefer `pub(crate)` for internal sharing

---

## Error handling
[ID: rust-lib-errors]

- Library crates: define error types with `thiserror` — implement `std::error::Error`,
  expose variants that callers can match on
- Binary crates and CLIs: use `anyhow::Result` for propagation — callers
  do not need to match on error variants
- Never use `.unwrap()` or `.expect()` in library code — propagate errors
  with `?`
- Use `.expect("reason")` in tests and examples only — the message must
  explain what went wrong, not just that it did
- Never panic in library code for recoverable conditions — return `Err`

---

## Ownership and borrowing
[ID: rust-lib-ownership]

- Prefer borrowing (`&T`, `&mut T`) over cloning in function signatures —
  clone only when ownership is genuinely required
- Use `Cow<'_, str>` for functions that accept both owned and borrowed strings
  when the choice depends on the caller's use case
- Avoid `Arc<Mutex<T>>` as a default — choose the right concurrency primitive
  for the access pattern (read-heavy → `RwLock`, single-owner → `Mutex`,
  immutable shared → `Arc<T>`)
- Document lifetime parameters with a comment when they are non-obvious

---

## Async conventions (if applicable)
[ID: rust-lib-async]

- Use `tokio` as the async runtime for libraries that must integrate with
  the tokio ecosystem; document the runtime requirement clearly
- Mark the runtime choice in `Cargo.toml` features — let callers opt in:
  `tokio = ["dep:tokio"]`
- Do not block inside an async function — use `tokio::task::spawn_blocking`
  for CPU-bound or blocking I/O work
- Prefer `async fn` in traits only with the `async-trait` crate or RPITIT
  (Rust 1.75+) — document the choice

---

## CLI conventions (if applicable)
[ID: rust-lib-cli]

- Parse arguments with `clap` (derive API) — never `std::env::args()` directly
- Exit codes: `0` success, `1` user/input error, `2` internal error —
  use `std::process::exit()` only in `main()`
- Write output to `stdout`; errors and diagnostics to `stderr`
- Support `--help` and `--version` — generated automatically by `clap`

---

## Rust conventions
[ID: rust-lib-conventions]

- Follow **Rust API Guidelines** (https://rust-lang.github.io/api-guidelines/)
  for library design — naming, documentation, type safety, and predictability
- All public items MUST have a doc comment (`///`) with at least one sentence
  describing what they do
- Include `# Examples` in doc comments for all public functions — examples
  are compiled and run as tests by `cargo test`
- Run `clippy` with at minimum `cargo clippy -- -D warnings` in CI —
  no clippy warnings allowed to merge
- `rustfmt` enforced — CI rejects unformatted code

---

## Testing
[EXTEND: base-testing]

- Unit tests in the same file as the code under test, in a `#[cfg(test)]`
  module — Rust convention; do not move them to a separate file
- Integration tests in `tests/` — compiled as separate crates, test only
  the public API
- Doc tests in `///` comments — run automatically with `cargo test`
- Use `proptest` or `quickcheck` for property-based testing of core algorithms
- Benchmark with `criterion` in `benches/` — run with `cargo bench`
- Test naming: `test_<unit_of_work>_<state>_<expected>`
  e.g. `test_parse_config_missing_field_returns_error`
- Run before every commit: `cargo test && cargo clippy -- -D warnings`

---

## Versioning and publishing
[ID: rust-lib-publishing]

- Semantic versioning — `MAJOR.MINOR.PATCH`; Cargo enforces semver for
  breaking API changes automatically via `cargo semver-checks`
- `CHANGELOG.md` updated on every release
- Publish to crates.io from CI only — never from a local machine
- `cargo publish --dry-run` in CI on PRs to catch packaging errors early
- Tag releases `vX.Y.Z` in git before publishing

---

## Git conventions
[EXTEND: base-git]

- `Cargo.lock` committed for binary crates; gitignored for library crates
- Do not commit `target/` — large build artefacts, fully reproducible

---

## Commands
```
cargo build              # compile (debug)
cargo build --release    # compile (optimised)
cargo test               # run all tests (unit + integration + doc tests)
cargo clippy -- -D warnings  # lint — fail on any warning
cargo fmt                # format all source files
cargo doc --open         # build and open documentation
cargo publish --dry-run  # verify crate before publishing
cargo publish            # publish to crates.io (CI only)
cargo bench              # run benchmarks
```