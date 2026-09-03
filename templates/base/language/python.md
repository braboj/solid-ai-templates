# Base — Python
[ID: base-python]
[DEPENDS ON: templates/base/core/quality.md]

Per-language tool selection for Python. `base-quality-gates` states which
categories a project MUST gate and at which layer; this file names the
Python tool that satisfies each. Stack templates add only the tools their
shape changes — a library's build and publish step, a service's runtime
checks — and do not re-declare the bindings below.

## Tooling
[ID: base-python-tooling]

| Category              | Tool                        | Config                    |
| --------------------- | --------------------------- | ------------------------- |
| Commit-hook framework | `pre-commit`                | `.pre-commit-config.yaml` |
| Lint                  | `ruff`                      | `pyproject.toml`          |
| Format                | `ruff format`               | `pyproject.toml`          |
| Type check            | `mypy` (strict)             | `pyproject.toml`          |
| Cognitive complexity  | `complexipy`                | `pyproject.toml`          |
| Security (SAST)       | `bandit`                    | `pyproject.toml`          |
| Tests                 | `pytest`                    | `pyproject.toml`          |
| Coverage              | `pytest-cov`                | `pyproject.toml`          |
| Mutation testing      | `mutmut`                    | `pyproject.toml`          |
| Docstrings            | `ruff` `D` rules            | `pyproject.toml`          |
| Package manifest      | `pyproject.toml`            | —                         |

- `ruff` MUST be the single lint and format tool. It subsumes flake8,
  isort, pyupgrade and most of pylint, so a project carrying those
  alongside it runs overlapping rule sets that disagree at the margins
- Cognitive complexity MUST be gated by a separate tool. `ruff` has no
  cognitive-complexity rule — its `C901` is McCabe, which measures a
  different thing — so the category has no Python binding without
  `complexipy`
- Tool configuration MUST live in `pyproject.toml`. Splitting it across
  `setup.cfg`, `tox.ini` or `.flake8` gives one tool two config sources
  whose precedence is tool-specific, and a rule edited in the losing file
  reads as applied
- `mypy` runs in strict mode. A non-strict run passes on unannotated
  code, so the gate reports success over the code least covered by it
- The coverage tool is named here; the threshold is not. The number and
  its escalation policy belong to `quality-gates-thresholds`, which
  governs every language
- Mutation testing is opt-in per `quality-gates-mutation`, and a project
  that has not adopted it carries no `mutmut` config. Prefer `mutmut`
  over `cosmic-ray` for a first adoption: it needs no session database
  to run, so the smallest useful run is one command against one module


## Optional and native dependencies
[ID: base-python-optional-deps]

A dependency that is heavy, native, or unavailable on some target
platform MUST be reached through one module that owns its import. The
alternative shape — a deferred `try`/`except ImportError` at each call
site — scatters the same handling across the package, repeats the
install hint wherever someone remembered it, and hides which dependency
is even optional.

```python
# pkg/_accel.py -- the only module that imports the optional backend
try:
    import accel
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "the native backend needs the 'accel' extra: pip install pkg[accel]"
    ) from exc
```

- The owning module MUST re-raise with an actionable message naming the
  extra and the command that installs it. A bare `ModuleNotFoundError`
  names the missing distribution, which is rarely the name the consumer
  has to install
- Consumers MUST import the owning module inside the function that needs
  it, never at module scope. Then `import pkg` succeeds in an
  environment without the extra, and the whole optional surface is one
  greppable import away
- The optional dependency MUST have its own entry in
  `[project.optional-dependencies]`, named for the capability it adds
  rather than the library behind it. The extra is the public name of the
  tier, and `base-quality` already requires a pluggable tier to be named
  for what it offers the caller
- Symbols the test suite monkeypatches MUST stay in a module that does
  not eager-import the heavy dependency. Where the seam sits behind the
  guarded import, every test needs the extra installed to patch it, and
  the boundary grows forwarding wrappers that duplicate signatures for
  no reason other than reachability
- `import pkg` succeeding without the extra is the checkable form of
  this rule, and it MUST be checked rather than assumed. In a clean
  environment run `pip install .` then
  `python -c "import pkg"` — the second command MUST exit 0. Run it as
  its own CI leg, because every other leg installs the extras and so
  cannot observe the failure

---

## Logging
[ID: base-python-logging]

A library MUST attach `logging.NullHandler()` to its own module logger
and install no writing handler. Without it `logging.lastResort` writes
records of WARNING and above to stderr, so a library that logs a warning
is heard whether or not the host asked to hear it.

```python
# pkg/transport.py -- the library core
import logging

_LOG = logging.getLogger(__name__)
_LOG.addHandler(logging.NullHandler())


class Transport:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._log = logger or _LOG
```

- The handler goes on the library's own logger, never on the root.
  Touching the root reconfigures logging for the whole host process
- The logger MUST be injectable, with the module logger as the fallback,
  so a caller keeps control of where output goes without reaching into
  the library's configuration
- The application tier of the same package MAY construct a writing
  handler, which is correct for an application. Copying that default
  into the library core is the defect: importing the library and
  constructing an object then writes to the host's stdout, and the host
  never asked. It is easy to reach for, because the application tier is
  already there and matching the surrounding convention is normally the
  right instinct
- The silence MUST be checked rather than assumed, in a fresh
  interpreter:

```bash
python -c "
import logging, pkg
handlers = logging.getLogger('pkg').handlers
assert handlers, 'the library attaches no handler'
assert all(isinstance(h, logging.NullHandler) for h in handlers), handlers
"
```

  It MUST exit 0. The fresh interpreter is the part that is easy to drop:
  a test runner that installs a root handler stops `lastResort` from ever
  firing, so an assertion that nothing reached stderr passes whether or
  not the library attached anything — the local value is correct and
  hides the missing guarantee.
