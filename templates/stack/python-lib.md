# Stack — Python Library / CLI
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/workflow/quality-gates.md, templates/base/core/examples.md]

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
  drops a whole sub-package from the scan while CI stays green
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
- All public API exported from `__init__.py`
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
- Lock file for reproducibility: `requirements-dev.lock` or equivalent
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

| Category | Layer 1 (editor) | Layer 2 (pre-commit) | Layer 3 (CI) | Config |
|----------|-----------------|---------------------|-------------|--------|
| Lint | Ruff | Ruff | Ruff | `pyproject.toml` |
| Format | Ruff | Ruff format | Ruff format --check | `pyproject.toml` |
| Type check | Pyright / mypy | mypy | mypy --strict | `pyproject.toml` |
| Docstrings | Ruff `D` rules | Ruff `D` rules | Ruff `D` rules | `pyproject.toml` (Google convention, `tests/**` exempt) |
| Security | — | — | Bandit + platform SAST | — |
| Secrets | — | gitleaks | gitleaks | `.pre-commit-config.yaml` |
| Tests | — | — | pytest | `pyproject.toml` |
| Coverage | — | — | pytest-cov ≥ 80% | `pyproject.toml` |
| Build | — | — | `python -m build` + `twine check dist/*` | `pyproject.toml` |

- Hook framework: `pre-commit` — config in `.pre-commit-config.yaml`
- Docstring convention: Google — enforced via Ruff `D` rules with
  `convention = "google"` in `pyproject.toml`
- Exempt the test suite from the `D` rules —
  `[tool.ruff.lint.per-file-ignores]` with `"tests/**" = ["D"]`.
  Docstrings on test functions are the busywork
  `quality-gates-exclusions` rules out, and without the exemption a
  freshly scaffolded project fails `ruff check` on its own tests. The
  naming convention under `base-testing` already carries a test's intent
