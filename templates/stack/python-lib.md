# Stack — Python Library / CLI
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/language/python.md, templates/base/core/cli.md, templates/base/workflow/quality-gates.md, templates/base/core/examples.md]

A Python library, CLI tool, or shared package intended to be imported or
installed. No web server, no frontend. May be published to PyPI.

---

## Stack
[ID: python-lib-stack]

- Language: Python 3.11+
- Package manager: [pip / uv / poetry]
- Build backend: [hatchling / setuptools / flit]
- Linter: ruff
- Formatter: ruff format
- Type checker: mypy (strict mode)
- Test runner: pytest
- Distribution: [PyPI / internal / not distributed]

---

## Project structure
[ID: python-lib-structure]

```
src/
  [package]/
    __init__.py
    [module].py
tests/
  test_[module].py
examples/
  README.md
  [pattern].py
pyproject.toml
README.md
CLAUDE.md
```

- Source layout (`src/`) — prevents accidental imports of the uninstalled
  package
- Check the claim against the built artifact, not the source tree. A
  wheel that starts carrying `tests/`, `scripts/` or a stray
  top-level module is invisible until someone installs it: lint,
  types, tests and coverage are all unchanged by it, and
  `twine check` does not look inside. Run this in the same CI job
  as `python -m build` and `twine check dist/*`, which is what
  makes the Build gate row mean what it says. Pass condition: the
  command prints nothing, and a missing wheel is a failure rather
  than a silent pass:

  ```bash
  py - <<'EOF'
import pathlib, zipfile

# The wheel is what a consumer installs, and nothing else in CI looks
# inside it. Run after `python -m build`.
wheels = sorted(pathlib.Path("dist").glob("*.whl"))
if not wheels:
    print("no wheel in dist/; run python -m build before this check")
for wheel in wheels:
    parts = wheel.name.split("-")
    expected = {parts[0], parts[0] + "-" + parts[1] + ".dist-info"}
    tops = {name.split("/")[0] for name in zipfile.ZipFile(wheel).namelist()}
    for extra in sorted(tops - expected):
        print("%s carries %s" % (wheel.name, extra))
  EOF
  ```

  One Python version is enough for a pure-Python wheel, so this
  does not need to join the test matrix
- `examples/` holds runnable usage patterns, governed by
  `base-examples`. Python specifics: under `src/` the directory cannot
  reach the wheel and needs no exclude — a flat layout MUST exclude it
  explicitly, like `tests/`; the smoke job installs with
  `pip install -e .` and no extra
- When adopting `src/` or adding a sub-package, audit every path-based
  exclude in tool configs (bandit `exclude_dirs`, coverage `omit`,
  ruff `extend-exclude`) for patterns that now match new package
  directories, and anchor them (`"./name"`). Verify by comparing
  scanned-file counts before and after — a colliding pattern silently
  drops a whole sub-package from the scan while CI stays green. This is
  one direction of the anchoring rule; `python-lib-packaging` states the
  other, for the include patterns of a build target
- When adopting `src/`, delete every `sys.path` manipulation from the
  test suite rather than repointing it — importing the package under
  test is the installation's job. Check: `grep -rn "sys.path" tests/`,
  output MUST be empty
- Prove the layout took by running the suite against an uninstalled
  package (`pip uninstall -y [package] && pytest --collect-only`) —
  collection MUST fail with `ModuleNotFoundError`. A suite that still
  passes has not adopted the layout, it has only moved files; the
  exclude audit above cannot detect this, because nothing collided
- After any path move the documentation references, execute every
  command the documentation prints from a clean environment and a
  neutral working directory — the repository root is the one place the
  old behaviour still appears to work, so a check run there passes for
  the wrong reason. No gate covers this: lint, types, tests, coverage
  and wheel contents are all unchanged by a move that breaks the
  README's headline example
- A quick start opening with `git clone` MUST carry an install step
  before the first command that imports the package. Any instruction to
  run from the repository root is a symptom of the layout the move is
  undoing, not a workaround for it
- All public API exported from `__init__.py`. Re-exporting a symbol runs
  its module at import time, so a package whose surface spans a cheap
  core and an expensive edge charges the edge's cost to every caller,
  including those that never touch it. Faced with that, a project
  usually picks between dropping the symbol from the root and breaking
  the rule, or re-exporting eagerly and taxing everyone
- A third option keeps both: bind the name on first access with a module
  `__getattr__`, so `from pkg import Thing` works and `import pkg` costs
  nothing extra. The `TYPE_CHECKING` import hands the checker the real
  class, without which the public API degrades to `Any` — which this
  template forbids

```python
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .heavy import Thing

_DEFERRED = {"Thing": "heavy"}


def __getattr__(name: str) -> object:
    submodule = _DEFERRED.get(name)

    if submodule is None:
        raise AttributeError(name)

    return getattr(import_module("." + submodule, __name__), name)
```

- The default stays eager. Deferral answers a measured cost, never a
  suspected one, and most packages never earn the indirection. Measure
  with `python -X importtime` first
- Record the measured number next to the mechanism, so the next reader
  re-measures rather than trusting it. A figure recorded once ages: one
  library's 70% import penalty re-measured at 38% on a later
  interpreter — half the recorded value, still real, and the difference
  is what decides whether the mechanism is still earning its place
- Pair the deferral with a test that a plain import loads neither the
  submodule nor its heavy dependency, or it regresses to eager the first
  time someone tidies the file. Check:
  `python -c "import pkg, sys; assert 'pkg.heavy' not in sys.modules"`,
  which MUST exit 0. Run it in a fresh interpreter — inside the suite
  the submodule is usually imported already, so the assertion passes or
  fails on unrelated state
- The map is also a rename table, and that is where a renamed public symbol
  keeps its old spelling. An entry keyed by the old name resolves to the
  module defining the new one, the removal version is stated beside it, and
  the resolver is the one place the deprecation warning goes rather than
  each call site. `from pkg import OldName` reaches it, because an import
  that misses the module namespace falls back to `__getattr__`

```python
# Old name -> new name. Both removed in 2.0.
_RENAMED = {"OldName": "NewName"}


def __getattr__(name: str) -> object:
    renamed = _RENAMED.get(name)

    if renamed is not None:
        warnings.warn(
            f"{name} is renamed to {renamed} and is removed in 2.0",
            DeprecationWarning,
            stacklevel=2,
        )
        name = renamed

    submodule = _DEFERRED.get(name)

    if submodule is None:
        raise AttributeError(name)

    return getattr(import_module("." + submodule, __name__), name)
```

- The alias costs one map entry and one branch, and retiring it is deleting
  the entry from a file the removal already touches — so no shim module is
  created and none is left behind to find. This is free only where the
  deferral already put a resolver: adding a module `__getattr__` purely to
  hold an alias buys the rename table at the cost of a resolver that every
  attribute miss now runs through
- Whether the old name stays in `__all__` is a separate decision from whether
  it resolves. Listing it keeps a star import working and advertises a name
  the project is retiring; omitting it retires the advertisement while the
  name still resolves for anyone who asks by it. A check that every
  advertised name resolves does not reach an alias kept out of the list, so
  the alias needs a test of its own
- No `setup.py` — use `pyproject.toml` only

---

## Python conventions
[ID: python-lib-conventions]

- Follow **PEP 8** for style — enforced by `ruff`; do not override ruff rules
  to work around style issues, fix the code instead
- Follow **PEP 257** for docstrings — Google docstring style; every public
  symbol MUST have a docstring
- Follow **PEP 484** and **PEP 526** for type annotations — all public
  functions and class members must be annotated
- No `Any` in public API — use specific types or `TypeVar`
- A sentinel a caller is expected to compare against is public API — export
  it beside the type whose fields carry it. The distinction an unset field
  preserves is only useful if someone can test for it, and
  `settings.timeout is UNSET` needs the name to resolve; keeping it private
  leaves a docstring reading "defaults to UNSET" beside a `package.UNSET`
  that raises `AttributeError`
- Make that sentinel a single-member enum rather than an instance of an
  ordinary class. A type checker narrows a union on identity against an enum
  member and not against a plain instance, so the class form hands the caller
  a guard they can write and cannot act on, and every call site then needs a
  cast the API cannot explain. The enum also supplies its own `__str__`,
  where a plain class falls back to `__repr__`, so a sentinel that renders as
  a caller-facing name overrides both spellings
- Keep functions small and single-purpose
- Raise specific exceptions — never bare `except:` or `except Exception:`
- No mutable default arguments

---

## Typing
[ID: python-lib-typing]

- Run mypy in strict mode: `mypy src/ --strict`
- Use `from __future__ import annotations` for forward references
- Prefer `collections.abc` types (`Sequence`, `Mapping`) over `list`, `dict`
  in public signatures
- Use `TypeAlias` for complex type aliases
- `--strict` is the target end-state, not always the day-one setting. A
  project on the scientific / data / ML stack (numpy, pandas, rdkit,
  native libs) whose deps ship no usable stubs would face a wall of
  unavoidable errors under `--strict` from the start. Adopt in stages:
  start non-strict with `ignore_missing_imports`, then per module flip
  `disallow_untyped_defs` + `strict_optional` and drop the
  missing-imports escape, converging on `--strict`
- Quarantine an untyped third-party lib with a per-module override
  (`follow_imports = "skip"`) AND a stated reason, rather than globally
  weakening the check — the escape stays visible and scoped to the
  library that needs it

---

## Testing
[EXTEND: base-testing]

- pytest for all tests
- Aim for 100% coverage of public API; use `# pragma: no cover` sparingly
- Use `pytest.mark.parametrize` for data-driven cases
- No mocks for pure functions — test with real inputs
- Component test naming: `test_<unit_of_work>_<state>_<expected>`
  e.g. `test_sum_negative_first_param_raises_value_error`
- Component tests in `tests/component/`, component integration tests in
  `tests/integration/`
- Run before every commit: `pytest && mypy src/ --strict`

---

## Packaging
[ID: python-lib-packaging]

- All metadata in `pyproject.toml` — no `setup.cfg`, no `setup.py`
- Pin minimum Python version in `requires-python`
- Do not pin exact versions in `dependencies` — use ranges (`>=`, `<`)
- A floor in a library's `dependencies` is a compatibility claim about
  consumers, not a record of what CI ran. Raising one narrows what a
  consumer may install without widening what is tested — CI resolves to
  the newest release satisfying each floor whatever the floors say.
  Move a floor only when a new version is genuinely required
- Set `versioning-strategy: increase-if-necessary` on the pip ecosystem
  in `.github/dependabot.yml` — the default `increase` lifts every floor
  to the newest release regardless. Applications, which pin rather than
  bound, keep the default. Leave the GitHub Actions ecosystem on its
  default: SHA pins there MUST keep moving
- Dev/test dependencies in `[project.optional-dependencies]` or
  `[dependency-groups]`
- Anchor every include pattern of a build target to the project root.
  A build backend reads an include the way git reads a `.gitignore`
  line, so a pattern carrying no separator matches at any depth:
  `include = ["src/pkg", "tests", "README.md", "LICENSE"]` looks exact
  and is not, because three of those four also select the same names
  inside any vendored directory or submodule. This is the exclude rule
  of `python-lib-structure` seen from the other side — an unanchored
  exclude over-matches and silently drops files from a scan, an
  unanchored include over-matches and silently adds files to an artifact
- No gate catches an over-matching include. Lint, types, tests and
  coverage are unchanged by it, `twine check` passes, and the wheel is
  usually correct because its `packages` entry already carries a
  separator. Only the sdist carries the extra files, and only listing it
  shows them
- Check: `python -m build`, then `tar -tzf dist/*.tar.gz` — the listing
  MUST contain no path under a vendored directory or submodule. Run it
  from a working checkout with submodules populated. A release workflow
  that checks out without submodules finds an empty directory, so the
  unanchored pattern selects nothing and the check passes while
  measuring nothing; adding `submodules: recursive` to that job for an
  SBOM or a docs build then ships the leak on the next tag, and nothing
  connects the two changes
- Lock the dev and test toolchain for reproducibility. The lock MUST be
  either universal — resolved across the whole `requires-python` range
  and every target platform, which is what `uv lock`, `poetry.lock` and
  `pdm.lock` produce — or one file per CI matrix leg, generated with an
  explicit target (`pip-compile --python-version`) and selected by the
  leg that matches
- A single `pip freeze` output MUST NOT be used where either a version
  matrix or a cross-platform contributor exists. Its markers are already
  resolved, so conditional dependencies are baked in or absent: on a
  `requires-python = ">=3.10"` project with a 3.10/3.13 matrix, `tomli`
  is present on one leg and absent on the other, and transitive pins
  diverge. The file installs on the leg that produced it and
  misrepresents the rest, which surfaces as a marker error that reads
  like a dependency bug
- CI MUST install from the lock with the flag that refuses a stale one —
  `uv sync --locked`, `poetry install` against a stale lock, `npm ci`,
  `cargo build --locked`. A lock nothing installs from records a
  resolution nobody runs: a dependency edit that skipped the relock
  installs a set the lock does not describe, and the committed file
  decays into decoration while still looking current
- Name what refreshes the lock, and when. An unrefreshed lock pins an
  ageing toolchain and emits no signal that it has aged, so the gate
  keeps passing against versions nobody chose
- If `__version__` derives from `importlib.metadata.version(...)`, an
  editable install reports a stale version after a `[project].version`
  bump until `pip install -e .` is rerun. Built artifacts (wheel, image)
  install fresh and are unaffected
- Rerunning the install does not always clear it. A leftover in-tree
  `*.egg-info` from an older build sits in the project root, which is on
  `sys.path` ahead of `site-packages`, so it shadows the freshly written
  `dist-info` and the version stays stale immediately after a clean
  reinstall. Delete it first: `rm -rf ./*.egg-info && pip install -e .`.
  Being gitignored is what keeps it invisible

---

## Git conventions
[EXTEND: base-git]

- Do not commit `.venv/`, `__pycache__/`, `*.egg-info/`, `dist/`, `.mypy_cache/`
- Tag releases and publish to PyPI from CI only — never from a local machine

---

## Commands
```
pip install -e ".[dev]"   # install with dev dependencies
pytest                    # run tests
mypy src/ --strict        # type check
ruff check src/ tests/    # lint
ruff format src/ tests/   # format
python -m build           # build distribution
twine check dist/*        # validate wheel/sdist metadata
```
---

## Quality gates
[EXTEND: base-quality-gates]

`base-python-tooling` names the tool for every category Python binds. This
section adds only what the library shape changes, and the layer each tool
runs at where it differs from the category default.

| Category | Layer 1 (editor) | Layer 2 (pre-commit) | Layer 3 (CI)                             |
| -------- | ---------------- | -------------------- | ---------------------------------------- |
| Secrets  | —                | gitleaks             | gitleaks                                 |
| Build    | —                | —                    | `python -m build` + `twine check dist/*` |

- Secret detection is not language-specific, so it binds here rather than
  in `base-python`: `gitleaks`, configured in `.pre-commit-config.yaml`
- The SAST scanner `base-python` binds runs alongside the hosted analysis
  the platform template supplies; neither replaces the other, and a
  platform that supplies none leaves the local scanner as the whole gate
- Docstrings are enforced at every layer, by the `D` rules of the linter
  `base-python` already binds — the category needs configuration here,
  not another tool
- A library's Build gate MUST validate distribution metadata, not only
  that the package compiles. `python -m build` produces the wheel and
  sdist; `twine check dist/*` is what fails on the metadata a package
  index would reject, and nothing else in the chain reads it
- Docstring convention: Google — enforced via Ruff `D` rules with
  `convention = "google"` in `pyproject.toml`
- Exempt the test suite from the `D` rules —
  `[tool.ruff.lint.per-file-ignores]` with `"tests/**" = ["D"]`.
  Docstrings on test functions are the busywork
  `quality-gates-exclusions` rules out, and without the exemption a
  freshly scaffolded project fails `ruff check` on its own tests. The
  naming convention under `base-testing` already carries a test's intent
